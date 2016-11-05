from urllib2 import urlopen, HTTPError, URLError
from time import sleep
from threading import Thread
from Queue import Queue


class UrlFetcher(object):
    MAX_READ_SIZE = 1024 * 1024

    def __init__(self, threads=12):
        self._input_queue = Queue()
        self._output_queue = None
        self._threads = threads
        self._is_closed = False
        self._delay = 0

        for _ in xrange(threads):
            t = Thread(target=self._process_urls)
            t.setDaemon(True)
            t.start()

    def _process_urls(self):
        while True:
            url = self._input_queue.get()
            if self._is_closed:
                break

            html = None
            try:
                html = urlopen(url, timeout=10).read(UrlFetcher.MAX_READ_SIZE)
            except HTTPError as e:
                print 'HTTP error: ' + str(e) + url
            except URLError as e:
                print 'URL error: ' + str(e) + url
            except Exception as e:
                print 'Exception while fetching: ' + str(e) + url

            self._output_queue.put((url, html))
            self._input_queue.task_done()
            sleep(self._delay)

    def set_output_queue(self, new_queue):
        self._output_queue = new_queue

    def enqueue_url(self, url):
        self._input_queue.put(url)

    def set_delay(self, new_delay):
        self._delay = new_delay if new_delay >= 0 else 0

    def get_threads_count(self):
        return self._threads

    def close(self):
        self._input_queue.join()
        self._is_closed = True
        for _ in xrange(self._threads):
            self._input_queue.put(None)
