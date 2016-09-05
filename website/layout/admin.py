from reversion.admin import VersionAdmin

from layout.models import Template
from website.admin import admin_site


admin_site.register(Template, VersionAdmin)
