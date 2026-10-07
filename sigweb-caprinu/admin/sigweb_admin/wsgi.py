"""WSGI do painel administrativo do SIGWeb (usado pelo gunicorn)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sigweb_admin.settings')

application = get_wsgi_application()
