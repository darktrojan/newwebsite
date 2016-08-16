from content.models import BlogEntry, Page

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext, Template


def test(request):
	page = get_object_or_404(Page, url=request.path)
	template = Template(page.as_template())
	context = RequestContext(request, {
		'title': page.title,
	})
	return HttpResponse(template.render(context))


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

	return render(request, 'layout/blog_list.html', {
		'entries': entries,
	})


def blog_entry(request, date, slug):
	entry = get_object_or_404(
		BlogEntry, created__year=date[0:4], created__month=date[5:7], slug=slug
	)
	return render(request, 'layout/blog_entry.html', {
		'title': entry.title,
		'entry': entry,
	})
