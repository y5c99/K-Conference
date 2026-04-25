"""
URLs for the 'accounts' app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Sign up — two steps
    path('signup/', views.signup_role, name='signup_role'),
    path('signup/details/', views.signup_details, name='signup_details'),

    # Login / logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard router + role dashboards
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/organiser/',   views.dashboard_organiser,
         name='dashboard_organiser'),
    path('dashboard/author/',      views.dashboard_author,
         name='dashboard_author'),
    path('dashboard/reviewer/',    views.dashboard_reviewer,
         name='dashboard_reviewer'),
    path('dashboard/participant/', views.dashboard_participant,
         name='dashboard_participant'),
]