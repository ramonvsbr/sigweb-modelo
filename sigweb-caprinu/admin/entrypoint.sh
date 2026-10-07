#!/bin/sh
# Prepara o painel e sobe o servidor.
#  1. migrate: cria as tabelas do próprio Django (usuários, sessões) no banco.
#     As tabelas do mapa NÃO são tocadas: os modelos são managed = False e o
#     esquema vem de banco_de_dados/.
#  2. cria o superusuário na primeira subida, se DJANGO_SUPERUSER_* estiver definido.
set -eu

python manage.py migrate --noinput

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    python manage.py createsuperuser --noinput \
        --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" \
        || echo "(superusuário já existe — mantido)"
fi

exec gunicorn sigweb_admin.wsgi:application \
    --bind 0.0.0.0:8000 --workers 2 --access-logfile -
