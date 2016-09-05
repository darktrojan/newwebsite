from django.db import models

import reversion


@reversion.register()
class Template(models.Model):
	name = models.CharField(max_length=32, unique=True)
	content = models.TextField()
	modified = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.name


class LayoutPermissions(models.Model):
	class Meta:
		managed = False
		permissions = ( 
			('admin', 'Can change templates and stylesheets'),
			('files', 'Can view files and images'),
		)
