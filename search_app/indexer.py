# -*- coding: utf-8 -*-
import multiprocessing
import threading
import unicodedata
from django.db.utils import IntegrityError
from .parser import Parser
from django.db import transaction
from collections import Counter
from .models import *
from nltk.tokenize import RegexpTokenizer
from nltk.stem.snowball import EnglishStemmer, RussianStemmer
from langdetect import detect


def start_url_processing(urls, depth, width, delay, one_domain):
    parser = Parser()
    for url in urls:
        results = parser.start_parsing(url, depth, width, delay, one_domain)
        threading.Thread(target=process_results, args=(results, url)).start()


def process_results(results, root_url):
    proc_pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())

    results = proc_pool.map(process_text, results)

    proc_pool.close()
    proc_pool.join()

    with Indexer.database_lock:
        indexer = Indexer()
        for url, words, lang in results:
            try:
                indexer.add_words_to_url(words, url, lang)
            except IntegrityError as e:
                print 'Integrity error for url {}'.format(url)
                print str(e)
            except Exception as e:
                print str(e)

    print root_url, 'finished'


def process_text(url_text):
    url, text = url_text

    try:
        language = detect(text)
    except Exception:
        language = ''

    toker = RegexpTokenizer(r'[^\W_]*-?[^\W_]+')
    words_on_page = toker.tokenize(text.lower())

    stemmer = None
    if language == 'ru':
        stemmer = RussianStemmer()
    elif language == 'en':
        stemmer = EnglishStemmer()

    if stemmer:
        words_on_page = [stemmer.stem(word) for word in words_on_page]

    return url, words_on_page, language


class Indexer(object):
    database_lock = threading.Lock()

    @transaction.atomic
    def add_words_to_url(self, words, url, lang):
        def strip_accents(s):
            return u''.join(c for c in unicodedata.normalize('NFD', s)
                            if unicodedata.category(c) != 'Mn')

        url_model, is_created = Url.objects.get_or_create(url=url,
                                                          language=lang)
        url_model.urlindex_set.all().delete()

        counter_dict = Counter(strip_accents(word) for word in words)
        url_model.words_count = sum(counter_dict.itervalues())

        all_words_to_add = set(counter_dict.iterkeys())
        words_in_db = set(
            Word.objects.filter(word__in=counter_dict.keys())
                .values_list('word', flat=True)
        )
        words_to_create = all_words_to_add - words_in_db

        url_model.save()
        Word.objects.bulk_create(Word(word=word) for word in words_to_create)
        indices = (UrlIndex(url=url_model, count=count,
                            word=Word.objects.get(word=word))
                   for word, count in counter_dict.iteritems())
        UrlIndex.objects.bulk_create(indices)
