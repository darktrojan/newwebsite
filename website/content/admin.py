from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from mptt.admin import DraggableMPTTAdmin

from content.models import BlogEntry, MenuEntry, Page
from layout.models import get_templates
from website.admin import admin_site


class PageAdmin(admin.ModelAdmin):
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

	change_list_template = 'admin/content/change_list.html'
	change_form_template = 'admin/content/change_form.html'

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

	def view_on_site(self, obj):
		return obj.url

	def view_on_site_inline(self, obj):
		return mark_safe('<a href="%s" class="viewsitelink">View on site</a>' % obj.url)
	view_on_site_inline.allow_tags = True
	view_on_site_inline.short_description = 'View on site'


class MenuEntryAdmin(DraggableMPTTAdmin):
	list_display = ('tree_actions', 'indented_title', 'href',)


class BlogEntryAdmin(admin.ModelAdmin):
	list_display = ('title', 'created', 'modified', 'view_on_site_inline',)
	ordering = ('-created',)
	prepopulated_fields = {'slug': ('title',)}

	def view_on_site(self, obj):
		return obj.get_absolute_url()

	def view_on_site_inline(self, obj):
		return mark_safe('<a href="%s" class="viewsitelink">View on site</a>' % obj.get_absolute_url())
	view_on_site_inline.allow_tags = True
	view_on_site_inline.short_description = 'View on site'

admin_site.register(Page, PageAdmin)
admin_site.register(MenuEntry, MenuEntryAdmin)
admin_site.register(BlogEntry, BlogEntryAdmin)
