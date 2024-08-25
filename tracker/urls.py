from django.urls import path
from . import views

app_name = 'tracker'
urlpatterns = [
    path('', views.IssueListView.as_view(), name='issue_list'),
    path('<int:pk>/', views.issue_detail, name='issue_detail'),    
    path('new/', views.issue_form, name='issue_create'),
    path('<int:pk>/edit/', views.issue_form, name='issue_edit'),
]