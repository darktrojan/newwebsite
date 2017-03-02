from datetime import date
import os, re

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.utils.feedgenerator import Atom1Feed
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from easy_thumbnails.alias import aliases
from easy_thumbnails.files import get_thumbnailer

from content.models import BlogEntry, Page, PageHistory
from website import settings


def page(request, extra_context=None):
	alias = request.path[request.path.rfind('/') + 1:]
	if alias == '':
		alias = 'home'
	page = get_object_or_404(Page, alias=alias)

	url = page.get_absolute_url()
	if request.path != url:
		return HttpResponseRedirect(url)

	is_editor = request.user.has_perm('content.add_page')
	if not is_editor and page.status != 'P':
		raise Http404

	if is_editor and 'revision' in request.GET:
		try:
			version = page.revisions.get(pk=request.GET['revision'])
			page.title = version.title
			page.content = version.content
			page.extra_header_content = version.extra_header_content
		except PageHistory.DoesNotExist:
			raise Http404

	context = {
		'site_name': settings.SITE_NAME,
		'page': page,
		'alias': page.alias,
		'title': page.title,
		'content': mark_safe(page.content),
		'extra_header_content': mark_safe(page.extra_header_content),
	}
	context.update(extra_context or {})

	return render(request, page.template, context)


@staff_member_required
def all_pages(request):
	pages = list()

	for p in Page.objects.all().order_by('url'):
		pages.append({
			'url': p.url,
			'title': p.title,
			'status': p.status
		})

	return JsonResponse(pages, safe=False)


def blog_list(request, year=None, date=None, tag=None, extra_context=None):
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

	if 'atom' in request.GET:
		feed = Atom1Feed(
			title=settings.SITE_NAME,
			description=None,
			link='%s://%s%s' % (request.scheme, request.META['HTTP_HOST'], request.path)
		)
		for entry in entry_list[:5]:
			feed.add_item(
				title=entry.title,
				description=entry.content,
				link=entry.get_absolute_url(),
				pubdate=entry.created,
				updateddate=entry.modified,
			)
		xml = feed.writeString('UTF-8')
		return HttpResponse(xml, content_type='application/atom+xml; charset=utf-8')

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

	context = {
		'site_name': settings.SITE_NAME,
		'title': 'News',
		'content': loader.render_to_string('content/blog_list.html', {
			'entries': entries,
		})
	}
	context.update(extra_context or {})

	return render(request, settings.NEWS_TEMPLATE_NAME, context)


def blog_entry(request, date, slug, extra_context=None):
	entry = get_object_or_404(
		BlogEntry, created__year=date[0:4], created__month=date[5:7], slug=slug
	)

	if not request.user.has_perm('content.add_blogentry') and entry.status != 'P':
		raise Http404

	context = {
		'site_name': settings.SITE_NAME,
		'title': entry.title,
		'content': loader.render_to_string('content/blog_entry.html', {
			'entry': entry,
		})
	}
	context.update(extra_context or {})

	return render(request, settings.NEWS_TEMPLATE_NAME, context)


@staff_member_required
@permission_required('layout.files')
def file_browser(request, template, path=None):
	# path is checked by urls
	if path is not None:
		root = os.path.join(settings.MEDIA_ROOT, template, path)
	else:
		root = os.path.join(settings.MEDIA_ROOT, template)

	if request.method == 'POST':
		kwargs = {'template': template}
		if 'upload' in request.FILES:
			uploaded_count = 0
			for f in request.FILES.getlist('upload'):
				new_file_name = re.sub(r'[^-\w \.]', '', f.name)
				if new_file_name and (template != 'images' or f.content_type.startswith('image/')):
					with open(os.path.join(root, new_file_name), 'wb') as destination:
						for c in f.chunks():
							destination.write(c)
					uploaded_count += 1
				else:
					pass  # TODO

			if uploaded_count > 0:
				messages.success(
					request, '%d %s uploaded.' %
					(uploaded_count, ngettext('file', 'files', uploaded_count))
				)
		elif 'new_folder_name' in request.POST:
				new_folder_name = request.POST['new_folder_name']
				new_folder_name = re.sub(r'[^-\w ]', '', new_folder_name)
				if new_folder_name:
					os.mkdir(os.path.join(root, new_folder_name))
					messages.success(request, 'Folder "%s" created successfully.' % new_folder_name)
					if path is None:
						kwargs['path'] = new_folder_name
					else:
						kwargs['path'] = os.path.join(path, new_folder_name)
					return HttpResponseRedirect(reverse('admin:file_browser', kwargs=kwargs))
				else:
					pass  # TODO
		elif request.POST.get('action') == 'delete_selected':
			deleted_count = 0
			for n in request.POST.getlist('_selected_action'):
				file_path = os.path.join(root, n)
				if os.path.exists(file_path):
					os.unlink(file_path)
					deleted_count += 1
			messages.success(
				request, '%d %s deleted.' %
				(deleted_count, ngettext('file', 'files', deleted_count))
			)
		elif request.POST.get('action') == 'move_selected':
			moved_count = 0
			destination = request.POST.get('action-destination')
			if destination == '':
				destination = os.path.join(settings.MEDIA_ROOT, template)
			else:
				destination = os.path.join(settings.MEDIA_ROOT, template, destination)

			for n in request.POST.getlist('_selected_action'):
				source_path = os.path.join(root, n)
				destination_path = os.path.join(destination, n)

				os.rename(source_path, destination_path)
				moved_count += 1

			messages.success(
				request, '%d %s moved.' %
				(moved_count, ngettext('file', 'files', moved_count))
			)

		if path is not None:
			kwargs['path'] = path
		return HttpResponseRedirect(reverse('admin:file_browser', kwargs=kwargs))

	dirs = []
	files = []
	parents = []
	if path is not None:
		dirs.append({
			'name': 'Parent folder',
			'url': reverse('admin:file_browser', kwargs={
				'template': template,
				'path': os.path.dirname(path)
			}),
			'path': os.path.dirname(path),
		})
		parents.append(os.path.basename(path))
		parent = os.path.dirname(path)
		while parent:
			parents.append(os.path.basename(parent))
			parent = os.path.dirname(parent)
		parents.reverse()

	for f in sorted(os.listdir(root), key=lambda x: x.lower()):
		f_path = os.path.join(root, f)
		if os.path.isdir(f_path):
			dirs.append({
				'name': f,
				'url': reverse('admin:file_browser', kwargs={
					'template': template,
					'path': f_path[len(settings.MEDIA_ROOT) + len(template) + 1:]
				}),
				'path': f_path[len(settings.MEDIA_ROOT) + len(template) + 1:],
			})
		elif os.path.isfile(f_path):
			files.append({
				'name': f,
				'path': f_path[len(settings.MEDIA_ROOT):],
				'mtime': date.fromtimestamp(os.path.getmtime(f_path)),
				'size': os.path.getsize(f_path),
			})

	from website.admin import admin_site
	context = dict(
		# Include common variables for rendering the admin template.
		admin_site.each_context(request),
		title='Image Manager' if template == 'images' else 'File Manager',
		template=template,
		parents=parents,
		path=path,
		dirs=dirs,
		files=files,
	)
	return render(request, 'admin/content/' + template[:-1] + '_browser.html', context)


@staff_member_required
def all_images(request):
	root = os.path.join(settings.MEDIA_ROOT, 'images')

	def do_folder(path):
		images = list()
		folders = list()
		for p in os.listdir(path):
			p = os.path.join(path, p)
			if (os.path.isdir(p)):
				folders.append(do_folder(p))
			elif p[-4:].lower() == '.svg':
				images.append({
					'url': os.path.join(settings.MEDIA_URL, p[len(settings.MEDIA_ROOT):]),
					'thumb': os.path.join(settings.MEDIA_URL, p[len(settings.MEDIA_ROOT):])
				})
				continue
			else:
				thumbnailer = get_thumbnailer(p[len(settings.MEDIA_ROOT):])
				existing = thumbnailer.get_existing_thumbnail(aliases.get('smallthumb'))
				d = {
					'url': os.path.join(settings.MEDIA_URL, p[len(settings.MEDIA_ROOT):])
				}
				if existing is not None:
					d['thumb'] = os.path.join(settings.MEDIA_URL, existing.name)
				images.append(d)

		return {
			'path': path[len(root) + 1:],
			'images': sorted(images, key=lambda x: x['url'].lower()),
			'folders': sorted(folders, key=lambda x: x['path'].lower())
		}

	return JsonResponse(do_folder(root), safe=False)


def get_thumbnail(request):
	t = get_thumbnailer(request.GET['f'])
	s = request.GET.get('s', 'smallthumb')
	g = t.get_thumbnail(aliases.get(s))
	return HttpResponseRedirect(os.path.join(settings.MEDIA_URL, g.name))
