import os

from textress.settings.base import *


DEBUG = False

ALLOWED_HOSTS = ['textress.com']

SITE_URL = "textress.com"

STRIPE_SECRET_KEY = os.environ['STRIPE_LIVE_SECRET_KEY']
STRIPE_PUBLIC_KEY = os.environ['STRIPE_LIVE_PUBLIC_KEY']

LOGGING_DIR = '/var/log/django'


# HTTPS
# os.environ['HTTPS'] = "on"
# os.environ['wsgi.url_scheme'] = 'https'
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SESSION_EXPIRE_AT_BROWSER_CLOSE=True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
