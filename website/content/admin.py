import difflib
from datetime import datetime
from pytz import UTC

from django.contrib import messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.html import escape, format_html
from django.utils.text import capfirst
from django.utils.timezone import now
from django.utils.translation import ngettext

from mptt.admin import DraggableMPTTAdmin

from content.models import BlogEntry, MenuEntry, Page, PageHistory, PUBLISH_STATUS_CHOICES
from layout.models import get_templates
from website.admin import admin_site


def view_on_site_inline(obj):
	return format_html('<a href="{}" target="_blank">View on site</a>', obj.get_absolute_url())
view_on_site_inline.short_description = 'View on site'


class PageAdmin(DraggableMPTTAdmin):
	mptt_indent_field = 'title'
	list_display = (
		'tree_actions', 'indented_title', 'alias',
		'status', 'modified', view_on_site_inline,
	)
	list_filter = ('status', 'template',)
	actions = ('change_template', 'change_status',)
	actions_on_top = False
	actions_on_bottom = True
	search_fields = ['alias', 'title']

	def changelist_view(self, request, extra_context=None):
		extra_context = extra_context or {}
		extra_context['template_names'] = get_templates()
		extra_context['statuses'] = PUBLISH_STATUS_CHOICES
		return super(PageAdmin, self).changelist_view(request, extra_context)

	def change_template(self, request, queryset):
		new_template = request.POST.get('action-template')
		updated = queryset.update(template=new_template)
		messages.success(request, '%d %s changed to %s' %
			(updated, ngettext('page', 'pages', updated), new_template)
		)
	change_template.short_description = u'Change template to\u2026'

	def change_status(modeladmin, request, queryset):
		new_status = request.POST.get('action-status')
		updated = queryset.update(status=new_status)
		for value, name in PUBLISH_STATUS_CHOICES:
			if value == new_status:
				break
		messages.success(request, '%d %s marked as %s' %
			(updated, ngettext('page', 'pages', updated), name.lower())
		)
	change_status.short_description = u'Mark selected pages as\u2026'

	def indented_title(self, item):
		return format_html(
			'<span style="margin-inline-start: {}px">{}</span>',
			item._mpttfield('level') * self.mptt_level_indent,
			item.title,
		)
	indented_title.short_description = 'Title'

	def url(self, item):
		return item.get_absolute_url()

	def view_on_site(self, obj):
		return obj.get_absolute_url()

	save_on_top = True
	fieldsets = ((None, {
		'fields': ('title', 'content',)
	}), ('Advanced options', {
		'classes': ('collapse',),
		'fields': ('alias', ('parent', 'template', 'status',), 'extra_header_content',),
	}),)

	def get_fieldsets(self, request, obj=None):
		if obj is None:
			return ((None, {
				'fields': (
					('title', 'alias',),
					('parent', 'template',),
					'content',
				)
			}), ('Advanced options', {
				'classes': ('collapse',),
				'fields': ('extra_header_content',),
			}),)

		if 'revision' in request.GET:
			fields = ['title', 'content', 'extra_header_content']
			if obj.revisions.get(pk=int(request.GET['revision'])).type == 'F':
				fields.append('modified')
			return ((None, {
				'fields': fields
			}),)
		return self.fieldsets

	def get_prepopulated_fields(self, request, obj):
		if obj is None or 'revision' not in request.GET:
			return {'alias': ('title',)}
		return {}

	def get_object(self, request, object_id, from_field=None):
		obj = super(PageAdmin, self).get_object(request, object_id, from_field)

		if 'revision' in request.GET:
			try:
				version = obj.revisions.get(pk=request.GET['revision'])
				obj.title = version.title
				obj.content = version.content
				obj.extra_header_content = version.extra_header_content
				obj.modified = version.modified
			except PageHistory.DoesNotExist:
				raise Http404

		return obj

	def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
		if extra_context is None:
			extra_context = {}

		if object_id is not None:
			obj = Page.objects.get(pk=object_id)
			if 'revision' in request.GET:
				try:
					extra_context['revision'] = obj.revisions.get(pk=request.GET['revision'])
				except Page.DoesNotExist, PageHistory.DoesNotExist:
					raise Http404
			elif obj.status == 'D' and not obj.history_set.exists():
				return HttpResponseRedirect('?revision=%d' % obj.draft_set.last().pk)

		return super(PageAdmin, self).changeform_view(request, object_id, form_url, extra_context)

	def save_model(self, request, obj, form, change):
		if change and '_newdraft' in request.POST:
			version = PageHistory(
				page=obj,
				type='D',
				title=obj.title,
				content=obj.content,
				extra_header_content=obj.extra_header_content,
				modifier=request.user,
			)
			version.save()
			return

		if 'revision' in request.GET:
			try:
				version = obj.revisions.get(pk=request.GET['revision'])
			except PageHistory.DoesNotExist:
				raise Http404

			if '_publish' in request.POST:
				version.delete()
				obj.status = 'P'
			else:
				version.title = obj.title
				version.content = obj.content
				version.extra_header_content = obj.extra_header_content
				if version.type == 'D':
					version.modified = datetime.now(UTC)
				elif version.type == 'F':
					version.modified = obj.modified
				version.save()
				return

		obj.modified = now()
		obj.modifier = request.user
		super(PageAdmin, self).save_model(request, obj, form, change)

	def response_add(self, request, obj):
		response = super(PageAdmin, self).response_add(request, obj)

		if '_newdraft' in request.POST:
			response['location'] = '%s?revision=%d' % (
				reverse('admin:content_page_change', args=(obj.pk,)), obj.draft_set.first().pk
			)

		return response

	def response_change(self, request, obj):
		response = super(PageAdmin, self).response_change(request, obj)

		if 'revision' in request.GET and '_continue' in request.POST:
			response['location'] = '?revision=%d' % int(request.GET['revision'])

		if '_newdraft' in request.POST:
			response['location'] = '?revision=%d' % obj.draft_set.first().pk

		if '_publish' in request.POST:
			response['location'] = reverse('admin:content_page_change', args=(obj.pk,))

		return response

	def history_view(self, request, object_id, extra_context=None):
		model = self.model
		obj = self.get_object(request, unquote(object_id))
		opts = model._meta

		if obj is None:
			raise Http404('%(name)s object with primary key %(key)r does not exist.' % {
				'name': force_text(model._meta.verbose_name),
				'key': escape(object_id),
			})

		if not self.has_change_permission(request, obj):
			raise PermissionDenied

		context = dict(
			self.admin_site.each_context(request),
			title='Versions: ' + str(obj),
			object=obj,
			opts=opts,
			module_name=capfirst(force_text(opts.verbose_name_plural)),
			preserved_filters=self.get_preserved_filters(request),
		)

		if request.method == 'POST' and '_makecurrent' in request.POST:
			try:
				current_version = obj.revisions.get(pk=request.GET['revision'])
				current_version.make_current(request.user)
				return HttpResponseRedirect(reverse('admin:content_page_history', args=(object_id,)))

			except PageHistory.DoesNotExist:
				raise Http404

		if 'revision' in request.GET:
			def _format_line(self, side, flag, linenum, text):
				try:
					linenum = '%d' % linenum
				except TypeError:
					# handle blank lines where linenum is '>' or ''
					pass
				# replace those things that would get confused with HTML symbols
				text = text.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;')

				return '<td>%s</td><td>%s</td>' % (linenum, text)

			differ = difflib.HtmlDiff()
			setattr(differ, '_table_template', '<table class="diff">%(data_rows)s</table>')
			setattr(difflib.HtmlDiff, '_format_line', _format_line)

			try:
				previous = ['']
				current_version = obj.revisions.get(pk=request.GET['revision'])
				if 'compare' in request.GET:
					previous_version = obj.revisions.get(pk=request.GET['compare'])
				elif current_version.type in ['D', 'F']:
					previous_version = obj
				else:
					previous_version = obj.revisions.filter(pk__lt=request.GET['revision']).last()
				if previous_version is not None:
					previous = previous_version.content.splitlines()
				current = current_version.content.splitlines()
				current_version.diff = differ.make_table(previous, current, context=True, numlines=4)
				context['this_version'] = current_version
				context['previous_revision'] = obj.history_set.filter(pk__lt=current_version.pk).first()
				context['next_revision'] = obj.history_set.filter(pk__gt=current_version.pk).last()
			except PageHistory.DoesNotExist:
				raise Http404

		context.update(extra_context or {})

		return TemplateResponse(request, "admin/content/page/object_history.html", context)

	class Media:
		# Replace built-in URLify function with my own since I want a different
		# behaviour. This means both files run but I see no way around it.
		js = ('admin/content/urlify.js',)


class MenuEntryAdmin(DraggableMPTTAdmin):
	list_display = ('tree_actions', 'indented_title', 'href',)

	def indented_title(self, item):
		return format_html(
			'<span style="margin-inline-start: {}px">{}</span>',
			item._mpttfield('level') * self.mptt_level_indent,
			item,
		)
	indented_title.short_description = 'Title'


class BlogEntryAdmin(ModelAdmin):
	list_display = ('title', 'status', 'modified', view_on_site_inline,)
	list_filter = ('status',)
	actions = ('make_published',)
	ordering = ('-created',)

	def make_published(modeladmin, request, queryset):
		queryset.update(status='P')
	make_published.short_description = 'Mark selected entries as published'

	def view_on_site(self, obj):
		return obj.get_absolute_url()

	change_form_template = 'admin/content/edit_change_form.html'
	save_on_top = True
	fields = (('title', 'slug',), ('tags', 'status',), 'content',)
	prepopulated_fields = {'slug': ('title',)}

	def save_model(self, request, obj, form, change):
		obj.modifier = request.user
		super(BlogEntryAdmin, self).save_model(request, obj, form, change)

	class Media:
		# Replace built-in URLify function with my own since I want a different
		# behaviour. This means both files run but I see no way around it.
		js = ('admin/content/urlify.js',)

admin_site.register(Page, PageAdmin)
admin_site.register(MenuEntry, MenuEntryAdmin)
admin_site.register(BlogEntry, BlogEntryAdmin)
