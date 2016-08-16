import os

from django.conf import settings
from django.db import models


def get_templates():
	templates = []
	root = os.path.join(settings.MEDIA_ROOT, 'templates')
	for f in sorted(os.listdir(root), key=lambda x: x.lower()):
		path = os.path.join(root, f)
		if os.path.isfile(path):
			templates.append((f[:-5], f[:-5]))
	return templates


class LayoutPermissions(models.Model):
	class Meta:
		managed = False
		permissions = ( 
			('admin', 'Can change templates and stylesheets'),
			('files', 'Can view files and images'),
		)
