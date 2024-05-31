from django.urls import path

from . import views

app_name = 'fotd'
urlpatterns = [
    path('', views.index, name='index'),
    path('fb/<yy>/', views.fb, name='fb'),

    path('detail/<fid>/', views.detail, name='detail'),
    path('feature/<fid>/', views.feature, name='feature'),
    path('ajax_feature_update/<fid>/', views.ajax_feature_update, name='ajax_feature_update'),
    path('ajax_feature_status/<fid>/', views.ajax_feature_status, name='ajax_feature_status'),

    path('task/<tid>/', views.task, name='task'),
    path('ajax_task_add/<fid>/', views.ajax_task_add, name='ajax_task_add'),
    path('ajax_task_update/<tid>/', views.ajax_task_update, name='ajax_task_update'),
    path('ajax_task_delete/<tid>/', views.ajax_task_delete, name='ajax_task_delete'),
    path('ajax_task_status/<tid>/', views.ajax_task_status, name='ajax_task_status'),
    
    path('backlog/<fid>/', views.backlog, name='backlog'),
]