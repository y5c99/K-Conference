"""
Django settings for kconference_project.
This file controls everything: which apps are loaded,
where templates and static files live, the database, etc.
"""

from pathlib import Path

# BASE_DIR points to the top-level 'kconference' folder.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# For a student project this is fine. In real life, never commit this.
SECRET_KEY = 'django-insecure-change-me-in-production-please-12345'

# DEBUG = True shows nice error pages while developing.
# Turn this off (False) in production.
DEBUG = True

# Hosts allowed to serve this app. '*' means anyone (fine for local dev).
ALLOWED_HOSTS = ['*']


# ---- Installed apps ----
# Django needs to know which apps exist. The first six are built-in.
# The last five are OUR apps.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Our apps
    'accounts',
    'conference',
    'submissions',
    'reviews',
    'core',
]

# ---- Middleware ----
# Middleware = small pieces of code that run on every request.
# We use Django's defaults (security, sessions, CSRF protection, etc.)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# The main URL configuration file.
ROOT_URLCONF = 'kconference_project.urls'

# ---- Templates ----
# This tells Django where to look for HTML files.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Look in the top-level 'templates/' folder we created.
        'DIRS': [BASE_DIR / 'templates'],
        # Also look inside each app's own 'templates/' folder.
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kconference_project.wsgi.application'


# ---- Database ----
# SQLite is a file-based database. Perfect for student projects.
# Django will create 'db.sqlite3' in your project folder automatically.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ---- Password validation ----
# Django checks that passwords aren't too weak.
AUTH_PASSWORD_VALIDATORS = [
]

#AUTH_PASSWORD_VALIDATORS = [
  #  {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    #{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    #{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    #{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
#]


# ---- Internationalisation ----
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True


# ---- Static files (CSS, JavaScript) ----
# URL prefix users see for static files in the browser.
STATIC_URL = 'static/'
# Folders Django searches when collecting static files.
STATICFILES_DIRS = [BASE_DIR / 'static']


# ---- Media files (uploaded by users) ----
# Later we'll upload paper PDFs. They go here.
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ---- Default primary key field type ----
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---- Login URLs ----
# Where Django sends users who try to access protected pages.
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'core:home'