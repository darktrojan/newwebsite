from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from mptt.admin import DraggableMPTTAdmin
from reversion.admin import VersionAdmin

from content.models import BlogEntry, MenuEntry, Page
from layout.models import Template
from website.admin import admin_site


class PageAdmin(VersionAdmin):
	list_display = ('url', 'title', 'modified', 'template', 'view_on_site_inline',)
	list_filter = ('template',)
	actions = ('change_template',)
	ordering = ('url',)

	# fieldsets = ((None, {
	# 	'fields': ('title', 'content',)
	# }), ('Advanced options', {
	# 	'classes': ('collapse',),
	# 	'fields': ('url', 'template',),
	# }),)

	change_list_template = 'admin/content/page/change_list.html'
	change_form_template = 'admin/content/htmledit_form.html'

	def changelist_view(self, request, extra_context=None):
		extra_context = extra_context or {}
		extra_context['templates'] = dict()
		for t in Template.objects.all():
			extra_context['templates'][t.pk] = t.name
		return super(PageAdmin, self).changelist_view(request, extra_context)

	def change_template(self, request, queryset):
		new_template = request.POST.get('action-template')
		updated = queryset.update(template=new_template)
		messages.success(request, '%d %s changed to %s' %
			(updated, ngettext('page', 'pages', updated), Template.objects.get(pk=new_template).name)
		)
	change_template.short_description = u'Change template to\u2026'

	def view_on_site(self, obj):
		return obj.url

	def view_on_site_inline(self, obj):
		return mark_safe('<a href="%s" class="viewsitelink">View on site</a>' % obj.url)
	view_on_site_inline.allow_tags = True
	view_on_site_inline.short_description = 'View on site'


class MenuEntryAdmin(DraggableMPTTAdmin):
	list_display = ('tree_actions', 'indented_title', 'href',)

	def indented_title(self, item):
		return format_html(
			'<span style="margin-inline-start: {}px">{}</span>',
			item._mpttfield('level') * self.mptt_level_indent,
			item,
		)
	indented_title.short_description = 'Title'


class BlogEntryAdmin(admin.ModelAdmin):
	list_display = ('title', 'created', 'modified', 'view_on_site_inline',)
	ordering = ('-created',)
	prepopulated_fields = {'slug': ('title',)}

	change_form_template = 'admin/content/htmledit_form.html'

	def view_on_site(self, obj):
		return obj.get_absolute_url()

	def view_on_site_inline(self, obj):
		return mark_safe('<a href="%s" class="viewsitelink">View on site</a>' % obj.get_absolute_url())
	view_on_site_inline.allow_tags = True
	view_on_site_inline.short_description = 'View on site'

admin_site.register(Page, PageAdmin)
admin_site.register(MenuEntry, MenuEntryAdmin)
admin_site.register(BlogEntry, BlogEntryAdmin)
