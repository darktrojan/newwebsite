from datetime import date
import os, re

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.utils.translation import ngettext

from easy_thumbnails.alias import aliases
from easy_thumbnails.files import get_thumbnailer

from website.admin import admin_site

CSS_ROOT = os.path.join(settings.MEDIA_ROOT, 'css')
CSS_EXTENSION = '.css'


@staff_member_required
@permission_required('layout.admin')
def css_list(request):
	if request.method == 'POST':
		varname = 'new_css'
		if varname in request.POST:
			file_name = request.POST[varname]
			file_path = os.path.join(CSS_ROOT, file_name + CSS_EXTENSION)
			if os.path.exists(file_path):
				messages.error(request, 'Stylesheet "%s" already exists.' % file_name)
				return HttpResponseRedirect(reverse('css_list'))

			os.mknod(file_path)
			messages.success(request, 'Stylesheet "%s" created successfully.' % file_name)
			return HttpResponseRedirect(
				reverse('css_edit', kwargs={'file_name': file_name})
			)

		varname = 'delete_css'
		if varname in request.POST:
			deleted_count = 0
			for file_name in request.POST.getlist(varname):
				file_path = os.path.join(CSS_ROOT, file_name + CSS_EXTENSION)
				if os.path.exists(file_path):
					os.unlink(file_path)
					deleted_count += 1

			if deleted_count:
				messages.success(request, '%d stylesheet deleted successfully.' % deleted_count)
			return HttpResponseRedirect(reverse('css_list'))

	files = []
	for f in sorted(os.listdir(CSS_ROOT)):
		name = f[:-len(CSS_EXTENSION)]
		path = os.path.join(CSS_ROOT, f)
		if os.path.isfile(path):
			obj = {
				'name': name,
				'mtime': date.fromtimestamp(os.path.getmtime(path)),
				'size': os.path.getsize(path)
			}
			files.append(obj)
	context = dict(
		# Include common variables for rendering the admin template.
		admin_site.each_context(request),
		title='Stylesheets',
		files=files,
	)
	return render(request, 'layout/css_list.html', context)


@staff_member_required
@permission_required('layout.admin')
def css_edit(request, file_name):
	path = os.path.join(CSS_ROOT, file_name + CSS_EXTENSION)
	if request.method == 'POST':
		with open(path, 'w') as f:
			f.write(request.POST['file_content'])
		messages.success(request, 'Changes to stylesheet "%s" saved.' % file_name)
		if request.POST.get('_continue'):
			return HttpResponseRedirect(
				reverse('css_edit', kwargs={'file_name': file_name})
			)
		return HttpResponseRedirect(reverse('css_list'))

	with open(path, 'r') as f:
		file_content = f.read()

	return render(request, 'layout/css_edit.html', dict(
		admin_site.each_context(request),
		title='Change stylesheet',
		file_name=file_name,
		file_content=file_content,
	))


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
					return HttpResponseRedirect(reverse('file_browser', kwargs=kwargs))
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

		if path is not None:
			kwargs['path'] = path
		return HttpResponseRedirect(reverse('file_browser', kwargs=kwargs))

	dirs = []
	files = []
	parents = []
	if path is not None:
		dirs.append({
			'name': 'Parent folder',
			'url': reverse('file_browser', kwargs={'template': template, 'path': os.path.dirname(path)}),
		})
		parents.append(os.path.basename(path))
		parent = os.path.dirname(path)
		while parent:
			parents.append(parent)
			parent = os.path.dirname(parent)
		parents.reverse()

	for f in sorted(os.listdir(root), key=lambda x: x.lower()):
		f_path = os.path.join(root, f)
		if os.path.isdir(f_path):
			dirs.append({
				'name': f,
				'url': reverse('file_browser', kwargs={
					'template': template,
					'path': f_path[len(settings.MEDIA_ROOT) + len(template) + 1:]
				})
			})
		elif os.path.isfile(f_path):
			files.append({
				'name': f,
				'path': f_path[len(settings.MEDIA_ROOT):],
				'mtime': date.fromtimestamp(os.path.getmtime(f_path)),
				'size': os.path.getsize(f_path),
			})
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
	return render(request, 'layout/' + template + '.html', context)


@staff_member_required
def all_images(request):
	images = list()

	def do_folder(path):
		for p in os.listdir(path):
			p = os.path.join(path, p)
			if (os.path.isdir(p)):
				do_folder(p)
			else:
				thumbnailer = get_thumbnailer(p[len(settings.MEDIA_ROOT):])
				images.append({
					'url': os.path.join(settings.MEDIA_URL, p[len(settings.MEDIA_ROOT):]),
					'thumb': os.path.join(
						settings.MEDIA_URL, thumbnailer.get_thumbnail(aliases.get('smallthumb')).name
					),
				})

	do_folder(os.path.join(settings.MEDIA_ROOT, 'images'))

	return JsonResponse(images, safe=False)
