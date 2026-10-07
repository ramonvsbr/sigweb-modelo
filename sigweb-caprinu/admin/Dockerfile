FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Reúne o CSS/JS do admin. Não precisa de banco; a chave abaixo é só do build.
RUN SECRET_KEY=build-only DB_PASSWORD=x python manage.py collectstatic --noinput

# Sem root em runtime.
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app

EXPOSE 8000
# Via `sh`, para não depender do bit de execução do arquivo.
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
