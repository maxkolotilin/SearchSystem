from __future__ import division
from bs4 import BeautifulSoup
from .robots import RobotsAnalyzer, urlparse
from urlparse import urljoin
from .UrlFetcher import UrlFetcher, Thread
from Queue import Queue
from threading import Lock


class Parser(object):
    url_fetcher_lock = Lock()
    url_fetcher = UrlFetcher()
    IGNORE = ('jpg', 'png', 'py', 'pdf', 'doc', 'pps', 'ppt', 'pptx',
              'docx', 'xls', 'xlsx', 'rar', 'zip', 'mp3', 'waw', 'exe')

    @staticmethod
    def set_url_fetcher(threads):
        def close_old_fetcher(fetcher):
            with Parser.url_fetcher_lock:
                fetcher.close()

        old_fetcher = Parser.url_fetcher
        Parser.url_fetcher = UrlFetcher(threads)
        Thread(target=close_old_fetcher, args=(old_fetcher,)).start()

    def start_parsing(self, url, depth, width, delay=0, one_domain=True,
                      site_graph=None):
        with Parser.url_fetcher_lock:
            url_fetcher = Parser.url_fetcher
            visited_urls = {}           # key=url, value=depth
            fetched_urls = Queue()
            data = []
            urls_count_for_processing = 0

            if isinstance(url, unicode):
                url = url.encode('utf-8')
            url = url if url[-1] != '/' else url[:-1]

            robots = RobotsAnalyzer()
            robots.try_add_robot(url)

            if one_domain:
                parsed_url = urlparse(url)
                root_url = parsed_url.scheme + '://' + parsed_url.netloc

            url_fetcher.set_delay(delay)
            url_fetcher.set_output_queue(fetched_urls)

            if robots.can_fetch(url):
                url_fetcher.enqueue_url(url)
                visited_urls[url] = 1
                urls_count_for_processing += 1

            while urls_count_for_processing > 0:
                current_url, html = fetched_urls.get()
                urls_count_for_processing -= 1

                if site_graph is not None:
                    site_graph[current_url] = []

                page_data = None
                if html:
                    page_data = self.parse_html(html, current_url)

                if page_data:
                    page_text, page_urls = page_data
                    data.append((current_url, page_text))

                    enqueue_count = 0
                    current_depth = visited_urls[current_url]
                    if current_depth < depth:
                        for url in page_urls:
                            if url.endswith(Parser.IGNORE):
                                continue
                            if one_domain:
                                if not url.startswith(root_url):
                                    continue
                            else:
                                robots.try_add_robot(url)

                            if url not in visited_urls:
                                if robots.can_fetch(url):
                                    visited_urls[url] = current_depth + 1
                                    enqueue_count += 1
                                    url_fetcher.enqueue_url(url)

                                    if site_graph is not None:
                                        site_graph[current_url].append(url)

                                    if enqueue_count == width:
                                        break

                        urls_count_for_processing += enqueue_count

                    # debug
                    print 'url:    {}'.format(current_url)
                    print 'depth:  {}'.format(current_depth)
                    # print u'page urls for ' + url + ' ' + str(page_urls)

        return data

    def parse_html(self, html, current_url):
        """
        Returns visible text on page and list of urls on page
        :param current_url: url of html page
        :param html: html page
        """
        soup = BeautifulSoup(html, 'html.parser')
        if not soup.html:
            return None

        for unnecessary_stuff in soup(['script', 'style']):
            unnecessary_stuff.extract()
            # extract 'title', 'head'?

        text_on_page = soup.get_text()

        links = set()
        for link in soup.find_all('a', href=True):
            link = link['href']
            if not link.startswith('mailto:'):
                link = link.split('#')[0]
                if link and link[-1] == '/':
                    link = link[:-1]
                link = urljoin(current_url, link)

                if isinstance(link, unicode):
                    link = link.encode('utf-8')

                links.add(link)

        return text_on_page, links
