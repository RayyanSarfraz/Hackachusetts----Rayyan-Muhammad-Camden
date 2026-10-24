# syntax=docker/dockerfile:1

# ---- Base ---------------------------------------------------------------
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps. libpq is needed at runtime by psycopg; the rest aid builds.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

# Run as a non-root user. /data/chroma is pre-created so the chroma_data named
# volume mounted there inherits appuser ownership (Docker creates missing mount
# points as root, which appuser cannot write).
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app \
    && mkdir -p /data/chroma \
    && chown appuser:appuser /data/chroma
USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]

# ---- Development --------------------------------------------------------
FROM base AS development

ENV DJANGO_SETTINGS_MODULE=config.settings.development

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---- Production ---------------------------------------------------------
FROM base AS production

ENV DJANGO_SETTINGS_MODULE=config.settings.production

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
