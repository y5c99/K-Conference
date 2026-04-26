"""
Main URL configuration for K-Conference.
Each path() line says: "If the URL starts with X, hand it to Y."
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin site (built-in)
    path('admin/', admin.site.urls),

    # Our apps. Each app has its own urls.py.
    # An empty '' means: this is the root, the home page lives here.
    path('', include('core.urls')),

    # We'll fill these in during later phases. They're commented out for now.
     path('accounts/', include('accounts.urls')),
     path('conferences/', include('conference.urls')),
     path('submissions/', include('submissions.urls')),
    path('reviews/', include('reviews.urls')),
]

# During development, let Django serve uploaded files (the 'media' folder).
# In production you'd use a real web server for this.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT or settings.STATICFILES_DIRS[0])