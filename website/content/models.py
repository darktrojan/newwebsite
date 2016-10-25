from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from mptt.models import MPTTModel, TreeForeignKey
import reversion

from layout.models import TemplateField

PUBLISH_STATUS_CHOICES = (
	('P', 'Published'),
	('D', 'Draft'),
	('A', 'Archived'),
)


@reversion.register()
class Page(models.Model):
	url = models.CharField(max_length=255, unique=True)
	title = models.CharField(max_length=255)
	template = TemplateField()
	content = models.TextField()
	modified = models.DateTimeField(auto_now=True)
	status = models.CharField(max_length=1, choices=PUBLISH_STATUS_CHOICES)

	def __unicode__(self):
		return self.url


class MenuEntry(MPTTModel):
	label = models.CharField(max_length=255)
	href = models.CharField(max_length=255, blank=True, verbose_name='Links to')
	parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

	def __unicode__(self):
		return self.label

	class Meta:
		verbose_name_plural = 'menu entries'


@reversion.register()
class BlogEntry(models.Model):
	created = models.DateTimeField(default=timezone.now)
	modified = models.DateTimeField(auto_now=True)
	slug = models.SlugField(max_length=255)
	title = models.CharField(max_length=255, blank=False)
	content = models.TextField()
	tags = models.CharField(max_length=255, blank=True)
	status = models.CharField(max_length=1, choices=PUBLISH_STATUS_CHOICES)

	def __unicode__(self):
		return self.title

	def dateslug(self):
		return self.created.strftime('%Y-%m')

	def get_absolute_url(self):
		return reverse('blog_entry', kwargs={'date': self.dateslug(), 'slug': self.slug})

	def get_tags(self):
		return self.tags.split(' ')

	def set_tags(self, tags=[]):
		self.tags = ' '.join(tags)

	class Meta:
		verbose_name_plural = 'blog entries'
