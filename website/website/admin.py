from django.contrib.admin import AdminSite, site


class MyAdminSite(AdminSite):
	def __init__(self, *args, **kwargs):
		super(MyAdminSite, self).__init__(*args, **kwargs)
		self._registry.update(site._registry)

	# def get_app_list(self, *args, **kwargs):
	# 	app_list = super(MyAdminSite, self).get_app_list(*args, **kwargs)
	# 	app_list = sorted(app_list, key=lambda x: x['name'].lower(), reverse=True)
	# 	return app_list

	# site_header = 'Monty Python administration'
	index_template = 'website/admin_index.html'

admin_site = MyAdminSite(name='myadmin')
