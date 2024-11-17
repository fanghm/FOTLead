from django.contrib import admin

from .models import Link, Tag

admin.site.register(Tag)
admin.site.register(Link)
