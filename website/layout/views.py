from datetime import date
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render

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
	from website.admin import admin_site
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

	from website.admin import admin_site
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
				reverse('admin:layoutfile_change', kwargs={'file_type': file_type, 'file_name': file_name})
			)
		return HttpResponseRedirect(reverse('admin:layoutfile_list', kwargs={'file_type': file_type}))

	with open(path, 'r') as f:
		file_content = f.read()

	from website.admin import admin_site
	return render(request, 'layout/layoutfile_change.html', dict(
		admin_site.each_context(request),
		title='Edit %s %s' % (type_name.lower(), file_name),
		file_type=file_type,
		file_name=file_name,
		file_content=file_content,
		file_type_name_plural=type_name + 's',
	))
