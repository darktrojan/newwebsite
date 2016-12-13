from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BlogEntry, BlogEntryHistory, Page, PageHistory


@receiver(post_save, sender=Page, dispatch_uid='page_history_saver')
def page_history_saver(sender, **kwargs):
	instance = kwargs['instance']
	version = PageHistory(
		page=instance,
		title=instance.title,
		content=instance.content,
		extra_header_content=instance.extra_header_content
	)
	version.save()


@receiver(post_save, sender=BlogEntry, dispatch_uid='blog_entry_history_saver')
def blog_entry_history_saver(sender, **kwargs):
	instance = kwargs['instance']
	version = BlogEntryHistory(
		page=instance,
		title=instance.title,
		content=instance.content
	)
	version.save()
