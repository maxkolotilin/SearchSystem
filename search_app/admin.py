from django.contrib import admin
from . import models

# Register your models here.


class UrlIndexInline(admin.TabularInline):
    model = models.UrlIndex
    max_num = 50
    extra = 3


class WordAdmin(admin.ModelAdmin):
    inlines = [UrlIndexInline]
    list_display = ('word',)
    search_fields = ['word']


class UrlAdmin(admin.ModelAdmin):
    list_display = ('url', 'language', 'words_count')
    list_filter = ['language']
    search_fields = ['url']


class UrlIndexFormatter(admin.ModelAdmin):
    list_display = ('word', 'count', 'url_and_language')
    list_filter = ['url__language']
    search_fields = ['word__word']


admin.site.register(models.Word, WordAdmin)
admin.site.register(models.Url, UrlAdmin)
admin.site.register(models.UrlIndex, UrlIndexFormatter)
