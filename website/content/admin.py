import difflib

from django.contrib import messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.timezone import now
from django.utils.translation import ngettext

from mptt.admin import DraggableMPTTAdmin

from content.models import BlogEntry, MenuEntry, Page, PageHistory
from layout.models import get_templates
from website.admin import admin_site


def make_published(modeladmin, request, queryset):
	queryset.update(status='P')


def view_on_site_inline(obj):
	return mark_safe('<a href="%s">View on site</a>' % obj.url)
view_on_site_inline.short_description = 'View on site'


class PageAdmin(ModelAdmin):
	list_display = ('url', 'title', 'status', 'modified', 'template', view_on_site_inline,)
	list_filter = ('status', 'template',)
	actions = ('change_template', make_published,)
	ordering = ('url',)

	fieldsets = ((None, {
		'fields': (('title', 'url',), 'content',)
	}), ('Advanced options', {
		'classes': ('collapse',),
		'fields': ('template', 'status', 'extra_header_content',),
	}),)

	change_list_template = 'admin/content/page/change_list.html'
	change_form_template = 'admin/content/htmledit_form.html'

	def changelist_view(self, request, extra_context=None):
		extra_context = extra_context or {}
		extra_context['template_names'] = get_templates()
		return super(PageAdmin, self).changelist_view(request, extra_context)

	def change_template(self, request, queryset):
		new_template = request.POST.get('action-template')
		updated = queryset.update(template=new_template)
		messages.success(request, '%d %s changed to %s' %
			(updated, ngettext('page', 'pages', updated), new_template)
		)
	change_template.short_description = u'Change template to\u2026'
	make_published.short_description = 'Mark selected pages as published'

	def view_on_site(self, obj):
		return obj.url

	def save_model(self, request, obj, form, change):
		obj.modified = now()
		obj.modifier = request.user
		super(PageAdmin, self).save_model(request, obj, form, change)

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
			title='Change history: ' + str(obj),
			object=obj,
			opts=opts,
			module_name=capfirst(force_text(opts.verbose_name_plural)),
			preserved_filters=self.get_preserved_filters(request),
		)

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

		previous = ['']
		history = obj.pagehistory_set.all().order_by('-modified')
		if 'revision' in request.GET:
			try:
				current_version = history.get(pk=request.GET['revision'])
				if 'compare' in request.GET:
					previous_version = history.get(pk=request.GET['compare'])
				else:
					previous_version = history.filter(pk__lt=request.GET['revision']).first()
				if previous_version is not None:
					previous = previous_version.content.splitlines()
				current = current_version.content.splitlines()
				current_version.diff = differ.make_table(previous, current, context=True, numlines=4)
				context['history'] = [current_version]
			except PageHistory.DoesNotExist:
				raise Http404
		else:
			for h in sorted(history, key=lambda x: x.modified):
				current = h.content.splitlines()
				h.diff = differ.make_table(previous, current, context=True, numlines=4)
				previous = current
			context['history'] = history

		context.update(extra_context or {})

		return TemplateResponse(request, "admin/content/page/object_history.html", context)


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
	actions = (make_published,)
	ordering = ('-created',)
	prepopulated_fields = {'slug': ('title',)}

	change_form_template = 'admin/content/htmledit_form.html'
	make_published.short_description = 'Mark selected entries as published'

	def view_on_site(self, obj):
		return obj.get_absolute_url()

	def save_model(self, request, obj, form, change):
		obj.modifier = request.user
		super(PageAdmin, self).save_model(request, obj, form, change)

admin_site.register(Page, PageAdmin)
admin_site.register(MenuEntry, MenuEntryAdmin)
admin_site.register(BlogEntry, BlogEntryAdmin)
