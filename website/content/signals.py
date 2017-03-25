from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BlogEntry, BlogEntryHistory, Page, PageHistory


@receiver(post_save, sender=Page, dispatch_uid='page_history_saver')
def page_history_saver(update_fields=None, **kwargs):
	# To avoid saving a revision, use update_fields. MPTT adds update_fields with all the
	# non-MPTT fields, so we count them. This is hacky.
	if update_fields is not None and len(update_fields) < 8:
		return

	instance = kwargs['instance']
	version = PageHistory(
		page=instance,
		title=instance.title,
		content=instance.content,
		extra_header_content=instance.extra_header_content,
		modifier=instance.modifier
	)
	if instance.status == 'D':
		version.type = 'D'
	version.save()


@receiver(post_save, sender=BlogEntry, dispatch_uid='blog_entry_history_saver')
def blog_entry_history_saver(**kwargs):
	instance = kwargs['instance']
	version = BlogEntryHistory(
		entry=instance,
		title=instance.title,
		content=instance.content,
		modifier=instance.modifier
	)
	version.save()
