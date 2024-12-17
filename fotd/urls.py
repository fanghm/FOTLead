from django.contrib.auth.views import LoginView
from django.urls import path

from . import backlog_views, task_views, team_views, views

app_name = 'fotd'
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('fb/<yy>/', views.fb, name='fb'),
    path('detail/<fid>/', views.detail, name='detail'),
    path('feature/<fid>/', views.feature, name='feature'),
    path(
        'ajax_feature_update/<fid>/',
        views.ajax_feature_update,
        name='ajax_feature_update',
    ),
    path(
        'ajax_feature_status/<fid>/',
        views.ajax_feature_status,
        name='ajax_feature_status',
    ),
    path('ajax_get_text2/<fid>/', views.ajax_get_text2, name='ajax_get_text2'),
    path('ajax_set_text2/<fid>/', views.ajax_set_text2, name='ajax_set_text2'),
    path(
        'ajax_send_email/<str:email_type>/',
        views.ajax_send_email,
        name='ajax_send_email',
    ),
    # team_views
    path('team/<pk>/', team_views.UpdateFeatureRolesView.as_view(), name='team'),
    # path('fot_add/<fid>/', team_views.fot_add, name='fot_add'),
    path('fot/<pk>/', views.fot, name='fot'),
    path('fot_add/<fid>/', views.fot_add, name='fot_add'),
    path(
        'ajax_add_feature_roles/<fid>/',
        views.ajax_add_feature_roles,
        name='ajax_add_feature_roles',
    ),
    path(
        'ajax_add_fot_members/<fid>/',
        views.ajax_add_fot_members,
        name='ajax_add_fot_members',
    ),
    # task_views
    path('task/<tid>/', task_views.edit_task, name='edit_task'),
    path('task/view/<tid>/', task_views.view_task, name='view_task'),
    path('ajax_task_add/<fid>/', task_views.ajax_task_add, name='ajax_task_add'),
    path(
        'ajax_task_update/<tid>/', task_views.ajax_task_update, name='ajax_task_update'
    ),
    path(
        'ajax_task_delete/<tid>/', task_views.ajax_task_delete, name='ajax_task_delete'
    ),
    path(
        'ajax_task_status/<tid>/', task_views.ajax_task_status, name='ajax_task_status'
    ),
    path(
        'add_program_boundary/', views.add_program_boundary, name='add_program_boundary'
    ),
    path(
        'ajax_program_boundary/',
        views.ajax_program_boundary,
        name='ajax_program_boundary',
    ),
    path('backlog/<fid>/', views.backlog, name='backlog'),
    path('ajax_get_item_links/<id>/', backlog_views.ajax_get_item_links, name='ajax_get_item_links'),
    path('ajax_update_item_links/<fid>/', backlog_views.ajax_update_item_links, name='ajax_update_item_links'),
]
