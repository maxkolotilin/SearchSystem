from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models

# Create your models here.


@python_2_unicode_compatible
class Word(models.Model):
    word = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.word


@python_2_unicode_compatible
class Url(models.Model):
    url = models.URLField(unique=True)
    language = models.CharField(max_length=5)
    words_count = models.IntegerField(default=0)

    def __str__(self):
        return 'url:{}; language: {}; words_count: {};'.format(
            unicode(self.url), unicode(self.language), unicode(self.words_count))


@python_2_unicode_compatible
class UrlIndex(models.Model):
    count = models.IntegerField()
    url = models.ForeignKey(Url)
    word = models.ForeignKey(Word)

    def url_and_language(self):
        return unicode(self.url.url) + ' | ' + unicode(self.url.language)

    def __str__(self):
        return '{} word: {}; count: {};'.format(
            unicode(self.url), unicode(self.word), str(self.count))
