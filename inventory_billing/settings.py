import os
from decimal import Decimal
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'replace-this-in-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'rest_framework',
    'items', 'customers', 'inventory.apps.InventoryConfig', 'billing', 'auth_user.apps.AuthUserConfig', 'notifications', 'reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'inventory_billing.urls'
TEMPLATES = [
    {'BACKEND': 'django.template.backends.django.DjangoTemplates','DIRS': [],
     'APP_DIRS': True,
     'OPTIONS': {'context_processors': [
         'django.template.context_processors.debug',
         'django.template.context_processors.request',
         'django.contrib.auth.context_processors.auth',
         'django.contrib.messages.context_processors.messages',
     ]}},
]
WSGI_APPLICATION = 'inventory_billing.wsgi.application'

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'dineshkumaran6040@gmail.com')

# Email backend configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'postbox5591@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'amkxwfatxtmjfcss')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

NOTIFICATIONS = {
    'DEFAULT_CHANNELS': ['email'],
    'LOW_STOCK_THRESHOLD': Decimal('5'),
    'BASE_URL': os.getenv('NOTIFICATIONS_BASE_URL', 'http://localhost:8000'),
    'ADMIN_CONTACTS': {
        'email': os.getenv('ADMIN_EMAILS', 'ops@example.com').split(','),
    },
    'SENDER_NAME': 'Inventory & Billing System',
    'CHANNELS': {
        'email': {
            'from_email': os.getenv('NOTIFY_FROM_EMAIL', DEFAULT_FROM_EMAIL),
        },
    },
}
