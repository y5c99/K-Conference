"""URLs for the 'core' app."""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Public home
    path('', views.home, name='home'),

    # Announcements (organiser-managed)
    path('conferences/<int:conference_pk>/announcements/',
         views.announcement_list, name='announcement_list'),
    path('conferences/<int:conference_pk>/announcements/new/',
         views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/edit/',
         views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/',
         views.announcement_delete, name='announcement_delete'),

    # FAQs (public list, organiser-managed)
    path('conferences/<int:conference_pk>/faq/',
         views.faq_list, name='faq_list'),
    path('conferences/<int:conference_pk>/faq/new/',
         views.faq_create, name='faq_create'),
    path('faq/<int:pk>/edit/', views.faq_edit, name='faq_edit'),
    path('faq/<int:pk>/delete/', views.faq_delete, name='faq_delete'),

    # Audit log
    path('conferences/<int:conference_pk>/audit/',
         views.audit_log, name='audit_log'),
    path('conferences/<int:conference_pk>/reports/',
         views.reports_dashboard, name='reports'),
    path('conferences/<int:conference_pk>/exports/<str:kind>/',
         views.export_csv, name='export_csv'),
]