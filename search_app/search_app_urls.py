from django.conf.urls import url
from . import views


app_name = 'search_app'

urlpatterns = [
    url(r'^$', views.index_page, name='start_page'),
    url(r'^search/$', views.SearchView.as_view(), name='search_page'),
    url(r'^indexing$', views.IndexView.as_view(), name='indexing_page'),
    url(r'^sitemap$', views.SitemapView.as_view(), name='sitemap_page'),
    url(r'^download$', views.DownloadView.as_view(), name='download'),
    url(r'^config$', views.ConfigView.as_view(), name='config_page'),
]
