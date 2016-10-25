import os.path

from django.db import models

from website import settings


def get_templates():
	templates = []
	root = os.path.join(settings.MEDIA_ROOT, 'templates')
	for f in sorted(os.listdir(root), key=lambda x: x.lower()):
		path = os.path.join(root, f)
		if os.path.isfile(path):
			templates.append(f)
	return templates


class TemplateField(models.FilePathField):
	def formfield(self, **kwargs):
		kwargs.update({
			'path': os.path.join(settings.MEDIA_ROOT, 'templates'),
			'match': r'\.html$'
		})
		field = models.FilePathField.formfield(self, **kwargs)
		new_choices = []
		for c in field.choices:
			new_choices.append((c[1], c[1]))
		field.choices = new_choices
		return field


# This class exists so that the layout app is registered with the admin site.
# Otherwise, bad things happen.
class FakeModel(models.Model):
	class Meta:
		pass


class LayoutPermissions(models.Model):
	class Meta:
		managed = False
		permissions = ( 
			('admin', 'Can change templates and stylesheets'),
			('files', 'Can view files and images'),
		)
