from content.models import BlogEntry, Page
from website import settings

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.utils.safestring import mark_safe

from reversion.models import Version


def page(request):
	page = get_object_or_404(Page, url=request.path)

	if not request.user.has_perm('content.add_page') and page.status != 'P':
		raise Http404

	if 'revision' in request.GET:
		try:
			version = Version.objects.get_for_object(page).get(id=request.GET['revision'])
			page.template = version.field_dict.get('template')
			page.title = version.field_dict.get('title')
			page.content = version.field_dict.get('content')
		except Version.DoesNotExist:
			pass

	return render(request, page.template, {
		'title': page.title,
		'content': mark_safe(page.content)
	})


def blog_list(request, year=None, date=None, tag=None):
	if year:
		entry_list = BlogEntry.objects.filter(created__year=year)
	elif date:
		entry_list = BlogEntry.objects.filter(created__year=date[0:4], created__month=date[5:7])
	elif tag:
		regex = r'(^|\b)' + tag + r'(\b|$)'
		entry_list = BlogEntry.objects.filter(tags__regex=regex)
	else:
		entry_list = BlogEntry.objects.all()

	if not request.user.has_perm('content.add_blogentry'):
		entry_list = entry_list.filter(status='P')

	entry_list = entry_list.order_by('-created')
	paginator = Paginator(entry_list, 5)

	page = request.GET.get('page')
	try:
		entries = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		entries = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		entries = paginator.page(paginator.num_pages)

	return render(request, settings.NEWS_TEMPLATE_NAME, {
		'title': 'News',
		'content': loader.render_to_string('content/blog_list.html', {
			'entries': entries,
		})
	})


def blog_entry(request, date, slug):
	entry = get_object_or_404(
		BlogEntry, created__year=date[0:4], created__month=date[5:7], slug=slug
	)

	if not request.user.has_perm('content.add_blogentry') and entry.status != 'P':
		raise Http404

	return render(request, settings.NEWS_TEMPLATE_NAME, {
		'title': entry.title,
		'content': loader.render_to_string('content/blog_entry.html', {
			'entry': entry,
		})
	})
