from reversion.admin import VersionAdmin

from layout.models import Template
from website.admin import admin_site


class TemplateAdmin(VersionAdmin):
	list_display = ('name', 'modified',)

admin_site.register(Template, TemplateAdmin)
