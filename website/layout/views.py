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

ROOTS = {
	'css': os.path.join(settings.MEDIA_ROOT, 'css'),
	'template': os.path.join(settings.MEDIA_ROOT, 'templates')
}
TYPE_NAMES = {
	'css': 'Stylesheet',
	'template': 'Template'
}


@staff_member_required
@permission_required('layout.admin')
def layoutfile_list(request, file_type):
	root = ROOTS[file_type]
	type_name = TYPE_NAMES[file_type]

	files = []
	for name in sorted(os.listdir(root)):
		path = os.path.join(root, name)
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
		title=type_name + 's',
		files=files,
		file_type=file_type,
		file_type_name=type_name,
		file_type_name_plural=type_name + 's',
	)
	return render(request, 'layout/layoutfile_list.html', context)


@staff_member_required
@permission_required('layout.admin')
def layoutfile_add(request, file_type):
	if request.method == 'POST':
		return layoutfile_change(request, file_type, request.POST['file_name'])

	type_name = TYPE_NAMES[file_type]

	return render(request, 'layout/layoutfile_change.html', dict(
		admin_site.each_context(request),
		title='Add %s' % type_name.lower(),
		file_type=file_type,
		file_type_name_plural=type_name + 's',
	))


@staff_member_required
@permission_required('layout.admin')
def layoutfile_change(request, file_type, file_name):
	path = os.path.join(ROOTS[file_type], file_name)
	type_name = TYPE_NAMES[file_type]
	if request.method == 'POST':
		with open(path, 'w') as f:
			f.write(request.POST['file_content'].replace('\r', '').encode('utf-8'))
		messages.success(request, 'Changes to %s "%s" saved.' % (type_name, file_name))
		if request.POST.get('_continue'):
			return HttpResponseRedirect(
				reverse('layoutfile_change', kwargs={'file_type': file_type, 'file_name': file_name})
			)
		return HttpResponseRedirect(reverse('layoutfile_list', kwargs={'file_type': file_type}))

	with open(path, 'r') as f:
		file_content = f.read()

	return render(request, 'layout/layoutfile_change.html', dict(
		admin_site.each_context(request),
		title='Edit %s %s' % (type_name.lower(), file_name),
		file_type=file_type,
		file_name=file_name,
		file_content=file_content,
		file_type_name_plural=type_name + 's',
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
		return HttpResponseRedirect(reverse('file_browser', kwargs=kwargs))

	dirs = []
	files = []
	parents = []
	if path is not None:
		dirs.append({
			'name': 'Parent folder',
			'url': reverse('file_browser', kwargs={'template': template, 'path': os.path.dirname(path)}),
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
				'url': reverse('file_browser', kwargs={
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
			elif p[-4:].lower() == '.svg':
				continue
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
