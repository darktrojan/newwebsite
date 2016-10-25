from django.contrib.admin import AdminSite, site
from django.core.urlresolvers import reverse


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
				'admin_url': reverse('file_browser', kwargs={'template': 'files'}),
			}
			images_model = {
				'name': 'Images',
				'object_name': 'images',
				'admin_url': reverse('file_browser', kwargs={'template': 'images'}),
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
				'admin_url': reverse('layoutfile_list', kwargs={'file_type': 'css'}),
				'add_url': reverse('layoutfile_add', kwargs={'file_type': 'css'}),
			}
			templates_model = {
				'name': 'Templates',
				'object_name': 'template',
				'admin_url': reverse('layoutfile_list', kwargs={'file_type': 'template'}),
				'add_url': reverse('layoutfile_add', kwargs={'file_type': 'template'}),
			}
			if label == 'layout':
				app_dict['models'] = [css_model, templates_model]
			elif 'layout' in app_dict:
				app_dict['layout']['models'] = [css_model, templates_model]

		return app_dict

	index_template = 'website/admin_index.html'

admin_site = MyAdminSite(name='myadmin')
