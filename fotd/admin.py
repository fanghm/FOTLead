from django.contrib import admin
from .models import Feature, FeatureRoles, TeamMember, Task, StatusUpdate, Link

# Register your models here.
admin.site.register(Feature)
admin.site.register(FeatureRoles)
admin.site.register(TeamMember)
admin.site.register(Task)
admin.site.register(StatusUpdate)
admin.site.register(Link)