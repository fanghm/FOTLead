from django.contrib import admin
from .models import Feature, FeatureUpdate, FeatureRoles, TeamMember, Task, StatusUpdate, Link, Sprint

# Register your models here.
admin.site.register(Feature)
admin.site.register(FeatureUpdate)
admin.site.register(FeatureRoles)
admin.site.register(TeamMember)
admin.site.register(Task)
admin.site.register(StatusUpdate)
admin.site.register(Link)
admin.site.register(Sprint)