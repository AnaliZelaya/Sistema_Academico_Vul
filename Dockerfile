FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py init_db.py schema.sql ./
COPY templates ./templates
COPY static ./static

RUN mkdir -p /app/db /app/uploads

EXPOSE 5000

CMD ["sh", "-c", "python init_db.py && exec gunicorn --workers ${GUNICORN_WORKERS:-3} --bind 0.0.0.0:5000 --access-logfile - --error-logfile - app:app"]
