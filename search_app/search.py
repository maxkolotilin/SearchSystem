from collections import defaultdict
from .models import *
from nltk.stem.snowball import EnglishStemmer, RussianStemmer
from math import log


def _tf_idf(url_indices):
    score_of_site = defaultdict(float)
    documents_with_word = {}
    number_of_documents = float(Url.objects.count())

    for url_index in url_indices:
        word = url_index.word.word
        url = url_index.url.url
        words_in_document = url_index.url.words_count
        word_count = url_index.count

        tf = float(word_count) / words_in_document

        if word not in documents_with_word:
            documents_with_word[word] = url_indices.filter(
                word=url_index.word).count()

        idf = log(number_of_documents/documents_with_word[word])

        score_of_site[url] += tf * idf
        if word in url:
            score_of_site[url] += 0.01

    return score_of_site


def _by_count(url_indices):
    viewed_urls = set()
    score_of_site = defaultdict(float)

    for url_index in url_indices:
        word = url_index.word.word
        url = url_index.url.url
        word_count = url_index.count

        score_of_site[url] += word_count
        if word in url:
            score_of_site[url] += 25
        if url in viewed_urls:
            score_of_site[url] += 100
        viewed_urls.add(url)

    return score_of_site


class Search(object):
    russian_stemmer = RussianStemmer()
    english_stemmer = EnglishStemmer()
    ranging_algorithms = [('tf_idf', _tf_idf), ('by_count', _by_count)]
    current_ranging_algorithm = ('tf_idf', _tf_idf)

    @staticmethod
    def process_query(query):
        tokens = [word for word in query.lower().split() if word]

        language = ''
        site = ''
        nostem = False
        for i in xrange(len(tokens)):
            if 'language:' in tokens[i]:
                language = tokens[i][9:]
                del tokens[i]
                break
        for i in xrange(len(tokens)):
            if 'site:' in tokens[i]:
                site = tokens[i][5:]
                del tokens[i]
                break
        for i in xrange(len(tokens)):
            if 'nostem:' in tokens[i]:
                if tokens[i][7:] == 'true':
                    nostem = True
                del tokens[i]
                break

        return tokens, language, site, nostem

    @staticmethod
    def get_url_indices(query_list, language, site):
        indices = UrlIndex.objects.filter(word__word__in=query_list)
        if site:
            indices = indices.filter(url__url__contains=site)
        if language:
            indices = indices.filter(url__language__contains=language)

        return indices

    @staticmethod
    def search(query_words, language='', site='', nostem=False):
        query_words = list(query_words)

        if not nostem:
            if language == 'ru':
                query_words = [Search.russian_stemmer.stem(word)
                               for word in query_words]
            elif language == 'en':
                query_words = [Search.english_stemmer.stem(word)
                               for word in query_words]
            else:
                query_words = [Search.russian_stemmer.stem(word)
                               for word in query_words] + \
                              [Search.english_stemmer.stem(word) for word in
                               query_words]

        indices = Search.get_url_indices(query_words, language, site)

        return Search.relevant_url_indices(indices).items()

    @staticmethod
    def relevant_url_indices(url_indices):
        name, ranging_algorithm = Search.current_ranging_algorithm
        return ranging_algorithm(url_indices)
