from django.urls import path

from . import views

app_name = 'fotd'
urlpatterns = [
    path('', views.index, name='index'),
    path('detail/<fid>/', views.detail, name='detail'),
    path('ajax_statusupdate/<tid>/', views.ajax_statusupdate, name='ajax_statusupdate'),
]