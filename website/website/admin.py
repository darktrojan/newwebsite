from django.conf.urls import url
from django.contrib.admin import AdminSite, site
from django.core.urlresolvers import reverse

import content.views, layout.views


class MyAdminSite(AdminSite):
	def __init__(self, *args, **kwargs):
		super(MyAdminSite, self).__init__(*args, **kwargs)
		self._registry.update(site._registry)

	def _build_app_dict(self, request, label=None):
		app_dict = super(MyAdminSite, self)._build_app_dict(request, label)

		if not app_dict:
			return app_dict

		if request.user.has_perm('layout.files'):
			files_model = {
				'name': 'Files',
				'object_name': 'files',
				'admin_url': reverse('admin:file_browser', kwargs={'template': 'files'}),
			}
			images_model = {
				'name': 'Images',
				'object_name': 'images',
				'admin_url': reverse('admin:file_browser', kwargs={'template': 'images'}),
			}

			if label == 'content':
				app_dict['models'].append(files_model)
				app_dict['models'].append(images_model)
			elif 'content' in app_dict:
				app_dict['content']['models'].append(files_model)
				app_dict['content']['models'].append(images_model)

		if request.user.has_perm('layout.admin'):
			css_model = {
				'name': 'Stylesheets',
				'object_name': 'css',
				'admin_url': reverse('admin:layoutfile_list', kwargs={'file_type': 'css'}),
				'add_url': reverse('admin:layoutfile_add', kwargs={'file_type': 'css'}),
			}
			templates_model = {
				'name': 'Templates',
				'object_name': 'template',
				'admin_url': reverse('admin:layoutfile_list', kwargs={'file_type': 'template'}),
				'add_url': reverse('admin:layoutfile_add', kwargs={'file_type': 'template'}),
			}
			if label == 'layout':
				app_dict['models'] = [css_model, templates_model]
			elif 'layout' in app_dict:
				app_dict['layout']['models'] = [css_model, templates_model]

		return app_dict

	def get_urls(self):
		urls = super(MyAdminSite, self).get_urls()
		my_urls = [
			url(
				r'^layout/(?P<file_type>css|template)/$',
				self.admin_view(layout.views.layoutfile_list), name='layoutfile_list'
			),
			url(
				r'^layout/(?P<file_type>css|template)/add/$',
				self.admin_view(layout.views.layoutfile_add), name='layoutfile_add'
			),
			url(
				r'^layout/(?P<file_type>css|template)/(?P<file_name>[-\w]+\.(css|html))/change/$',
				self.admin_view(layout.views.layoutfile_change), name='layoutfile_change'
			),
			url(
				r'^content/(?P<template>files|images)/(?P<path>[-\w/ ]+)?$',
				self.admin_view(content.views.file_browser), name='file_browser'
			),
			url(r'^content/all_pages$', content.views.all_pages),
			url(r'^content/all_images$', content.views.all_images),
			url(r'^content/get_thumbnail$', content.views.get_thumbnail),
		]
		return my_urls + urls

admin_site = MyAdminSite(name='myadmin')
