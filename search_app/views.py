from django.views.generic import TemplateView, View
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http.response import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from threading import Thread
from .indexer import start_url_processing
from .search import Search
from .parser import Parser
import pydot
import pdfkit


# Create your views here.

class SearchView(View):
    template_name = 'search_app/search.html'

    def get(self, request, *args, **kwargs):
        if 'query' not in request.GET:
            return HttpResponseRedirect(reverse('search_app:start_page'))

        words, lang, site, nostem = Search.process_query(request.GET['query'])

        urls = [url for url in Search.search(words, lang, site, nostem)]
        urls.sort(key=lambda x: x[1], reverse=True)

        context = {}
        context['urls'] = [url[0] for url in urls]
        context['query'] = ' '.join(words) + \
                           '; language:{}; site:{}; nostem:{}' \
                               .format(lang, site, nostem)

        return render(request, SearchView.template_name, context)


class DownloadView(TemplateView):
    page = None
    graph = None

    def get(self, request, *args, **kwargs):
        if 'pdf' in request.GET:
            pdf = pdfkit.from_string(DownloadView.page, False)
            response = HttpResponse(pdf, content_type='application/pdf')
            suffix = 'pdf'
        else:
            if DownloadView.graph:
                dot_graph = DownloadView.make_graph(DownloadView.graph)
            else:
                dot_graph = pydot.Dot(graph_type='digraph')

            if 'dot' in request.GET:
                response = HttpResponse(dot_graph.create_dot(),
                                        content_type='text/plain')
                suffix = 'gv'
            elif 'png' in request.GET:
                response = HttpResponse(dot_graph.create_png(),
                                        content_type='image/png')
                suffix = 'png'
            else:
                return HttpResponse('Error')

        site_name = DownloadView.graph.get('root', 'empty')
        response['Content-Disposition'] = \
            'attachment; filename="sitemap_{}.{}"' \
            .format(site_name, suffix)

        return response

    @staticmethod
    def make_graph(tree):
        def _make_graph(url, parent_node):
            for child_url in tree[url]:
                child_node = pydot.Node('"' + child_url.decode('utf-8') + '"')
                graph.add_node(child_node)
                graph.add_edge(pydot.Edge(parent_node, child_node))
                _make_graph(child_url, child_node)

        graph = pydot.Dot(graph_type='digraph')
        root_node = pydot.Node('"' + tree['root'].decode('utf-8') + '"')
        graph.add_node(root_node)
        _make_graph(tree['root'], root_node)

        return graph


class IndexView(TemplateView):
    template_name = 'search_app/parse.html'

    def post(self, request, *args, **kwargs):
        depth, width, delay, one_domain = parse_post(request)
        urls = request.POST['url']
        if 'file' in request.FILES:
            urls += ' ' + request.FILES['file'].read()
        urls = urls.split()

        task = Thread(target=start_url_processing, args=(urls, depth, width,
                                                         delay, one_domain))
        task.start()

        return HttpResponseRedirect(reverse('search_app:indexing_page'))


class SitemapView(TemplateView):
    template_name = 'search_app/sitemap_start.html'

    def post(self, request, *args, **kwargs):
        depth, width, delay, one_domain = parse_post(request)
        url = request.POST['url'].split()[0]
        parser = Parser()
        graph = {}

        parser.start_parsing(url, depth, width, delay, one_domain, graph)
        if graph:
            graph['root'] = url

        response = render_to_string('search_app/sitemap.html',
                                    {'graph': SitemapView.graph_to_html(graph),
                                     'site': url},
                                    request=request)
        DownloadView.page = response
        DownloadView.graph = graph

        return HttpResponse(response)

    @staticmethod
    def graph_to_html(graph):
        def get_parts(_url, _graph, parts, open_list, close_list):
            if open_list:
                parts.append('<ul>')

            parts.append('<li>')
            parts.append('<a href="{}">{}</a>'.format(_url, _url))
            close_flags = [False for _ in _graph[_url]]
            open_flags = [False for _ in _graph[_url]]
            if close_flags:
                close_flags[-1] = True
                open_flags[0] = True
            for child_url, open_flag, close_flag in \
                    zip(_graph[_url], open_flags, close_flags):
                get_parts(child_url, _graph, parts, open_flag, close_flag)
            parts.append('</li>')

            if close_list:
                parts.append('</ul>')

        parts_of_graph = []
        if graph:
            get_parts(graph['root'], graph, parts_of_graph, True, True)

        return ''.join(parts_of_graph)


class ConfigView(TemplateView):
    template_name = 'search_app/config.html'

    def get_context_data(self, **kwargs):
        context = super(ConfigView, self).get_context_data(**kwargs)
        name, algorithm = Search.current_ranging_algorithm
        context[name] = True
        context['threads'] = Parser.url_fetcher.get_threads_count()

        return context

    def post(self, request, *args, **kwargs):
        try:
            threads_count = int(request.POST['threads'])
        except ValueError:
            threads_count = 0
        algorithm = int(request.POST['ranging_alg'])

        Search.current_ranging_algorithm = Search.ranging_algorithms[algorithm]
        if 0 < threads_count != Parser.url_fetcher.get_threads_count():
            Parser.set_url_fetcher(threads_count)

        return HttpResponseRedirect(reverse('search_app:start_page'))


def index_page(request):
    return render(request, 'search_app/index.html')


def parse_post(request):
    try:
        depth = int(request.POST['depth_limit'])
    except ValueError:
        depth = 1
    try:
        width = int(request.POST['width_limit'])
    except ValueError:
        width = 1
    try:
        if 'delay' in request.POST:
            delay = float(request.POST['delay'].replace(',', '.'))
        else:
            delay = 0
    except ValueError:
        delay = 0
    one_domain = True if 'one_domain' in request.POST else False

    return depth, width, delay, one_domain
