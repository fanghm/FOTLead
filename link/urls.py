from django.urls import path

from . import views

app_name = "link"
urlpatterns = [
    path("", views.link_list, name="link_list"),
    path("add/", views.link_add, name="link_add"),
    path("edit/<int:pk>/", views.link_edit, name="link_edit"),
    path("approve/<int:pk>/", views.link_approve, name="link_approve"),
]
