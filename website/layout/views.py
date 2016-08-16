from datetime import date
import os, re

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ngettext

from content.models import Page
from website.admin import admin_site

ROOTS = {
	'template': os.path.join(settings.MEDIA_ROOT, 'templates'),
	'css': os.path.join(settings.MEDIA_ROOT, 'css'),
}
EXTENSIONS = {
	'template': '.html',
	'css': '.css',
}
HUMAN_NAMES = {
	'template': 'Template',
	'css': 'Stylesheet',
}


@staff_member_required
@permission_required('layout.admin')
def file_list(request):
	if request.method == 'POST':
		for t in ['css', 'template']:
			varname = 'new_' + t
			if varname in request.POST:
				file_name = request.POST[varname]
				file_path = os.path.join(ROOTS[t], file_name + EXTENSIONS[t])
				if os.path.exists(file_path):
					messages.error(request, '%s "%s" already exists.' % (HUMAN_NAMES[t], file_name))
					return HttpResponseRedirect(reverse('file_list'))

				os.mknod(file_path)
				messages.success(request, '%s "%s" created successfully.' % (HUMAN_NAMES[t], file_name))
				return HttpResponseRedirect(
					reverse('file_edit', kwargs={'file_type': t, 'file_name': file_name})
				)

			varname = 'delete_' + t
			if varname in request.POST:
				deleted_count = 0
				for file_name in request.POST.getlist(varname):
					file_path = os.path.join(ROOTS[t], file_name + EXTENSIONS[t])
					if os.path.exists(file_path):
						os.unlink(file_path)
						deleted_count += 1

				if deleted_count:
					messages.success(request, '%d %s deleted successfully.' % (deleted_count, HUMAN_NAMES[t]))
				return HttpResponseRedirect(reverse('file_list'))

	files = {}
	for file_type, root in ROOTS.iteritems():
		files[file_type] = []
		for f in sorted(os.listdir(root)):
			name = f[:-len(EXTENSIONS[file_type])]
			path = os.path.join(root, f)
			if os.path.isfile(path):
				obj = {
					'name': name,
					'mtime': date.fromtimestamp(os.path.getmtime(path)),
					'size': os.path.getsize(path)
				}
				if (file_type == 'template'):
					obj['page_count'] = Page.objects.filter(template=name).count()
				files[file_type].append(obj)
	context = dict(
		# Include common variables for rendering the admin template.
		admin_site.each_context(request),
		title='Layout',
		files=files,
	)
	return render(request, 'layout/file_list.html', context)


@staff_member_required
@permission_required('layout.admin')
def file_edit(request, file_type, file_name):
	path = os.path.join(ROOTS[file_type], file_name + EXTENSIONS[file_type])
	if request.method == 'POST':
		with open(path, 'w') as f:
			f.write(request.POST['file_content'])
		messages.success(request, 'Changes to %s "%s" saved.' % (HUMAN_NAMES[file_type], file_name))
		if request.POST.get('_continue'):
			return HttpResponseRedirect(
				reverse('file_edit', kwargs={'file_type': file_type, 'file_name': file_name})
			)
		return HttpResponseRedirect(reverse('file_list'))

	with open(path, 'r') as f:
		file_content = f.read()

	return render(request, 'layout/file_edit.html', dict(
		admin_site.each_context(request),
		title='Template Editor' if file_type == 'template' else 'Stylesheet Editor',
		file_name=file_name,
		file_content=file_content,
	))


@staff_member_required
@permission_required('layout.admin')
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

