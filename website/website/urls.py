import content.views
import layout.views

from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
# from django.contrib import admin

from website.admin import admin_site

urlpatterns = [
	url(
		r'^admin/layout/(?P<file_type>css|template)/$',
		admin_site.admin_view(layout.views.layoutfile_list), name='layoutfile_list'
	),
	url(
		r'^admin/layout/(?P<file_type>css|template)/add/$',
		admin_site.admin_view(layout.views.layoutfile_add), name='layoutfile_add'
	),
	url(
		r'^admin/layout/(?P<file_type>css|template)/(?P<file_name>[-\w]+\.(css|html))/change/$',
		admin_site.admin_view(layout.views.layoutfile_change), name='layoutfile_change'
	),
	url(
		r'^admin/(?P<template>files|images)/(?P<path>[-\w/ ]+)?$',
		admin_site.admin_view(layout.views.file_browser), name='file_browser'
	),
	url(r'^admin/all_images$', layout.views.all_images),
	url(r'^admin/', admin_site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
	url(r'^news/?$', content.views.blog_list, name='blog_list'),
	url(r'^news/tag/(?P<tag>[-\w]+)/?$', content.views.blog_list, name='blog_list'),
	url(r'^news/(?P<year>\d{4})/?$', content.views.blog_list, name='blog_list'),
	url(r'^news/(?P<date>\d{4}-\d{2})/?$', content.views.blog_list, name='blog_list'),
	url(
		r'^news/(?P<date>\d{4}-\d{2})/(?P<slug>[-\w]+)$',
		content.views.blog_entry, name='blog_entry'
	),
	url(r'^', content.views.page)
]
