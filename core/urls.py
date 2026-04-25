"""
URLs for the 'core' app. These handle simple public pages
like the home page and (later) FAQ + announcements.
"""

from django.urls import path
from . import views

# 'app_name' lets us refer to URLs as 'core:home' instead of just 'home'.
# This avoids name clashes between apps.
app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
]