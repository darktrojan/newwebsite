import content.views
import layout.views

from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
# from django.contrib import admin

from website.admin import admin_site

urlpatterns = [
	url(r'^admin/layout/css/$', admin_site.admin_view(layout.views.css_list), name='css_list'),
	url(
		r'^admin/layout/css/(?P<file_name>[-\w]+)$',
		admin_site.admin_view(layout.views.css_edit), name='css_edit'
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
	url(r'^', content.views.test)
]
