#!/bin/sh
set -e

# Wait for the database to accept connections before starting Django.
if [ -n "$DATABASE_URL" ] || [ -n "$POSTGRES_HOST" ]; then
    DB_HOST="${POSTGRES_HOST:-db}"
    DB_PORT="${POSTGRES_PORT:-5432}"
    echo "Waiting for database at $DB_HOST:$DB_PORT ..."
    until python -c "import socket,sys; s=socket.socket(); s.settimeout(2); sys.exit(0) if s.connect_ex(('$DB_HOST', $DB_PORT))==0 else sys.exit(1)" 2>/dev/null; do
        sleep 1
    done
    echo "Database is up."
fi

# Apply migrations and collect static files.
python manage.py migrate --no-input

# Development-only: seed clinical-trial data once, so a fresh `docker compose up`
# works with no manual steps. This NEVER runs in production — there, trial data
# is loaded deliberately via `python manage.py ingest_trials <csv>`.
#
# Guards: dev settings only, CSV must exist, and the Trial table must be empty
# (so we don't re-embed ~3k rows on every restart).
TRIALS_CSV="${TRIALS_CSV:-/data/source/trials/data.csv}"
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.development" ] && [ -f "$TRIALS_CSV" ]; then
    NEEDS_SEED="$(python -c "
import django, os
django.setup()
from apps.engine.models import Trial
try:
    print('yes' if Trial.objects.count() == 0 else 'no')
except Exception:
    print('no')
" 2>/dev/null)"
    if [ "$NEEDS_SEED" = "yes" ]; then
        echo "Seeding clinical-trial data from $TRIALS_CSV (dev, one-time)..."
        python manage.py ingest_trials "$TRIALS_CSV" || \
            echo "Trial seeding failed; continuing (retrieval will be unavailable)."
    else
        echo "Trial data already present (or unavailable); skipping seed."
    fi
fi

if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
    python manage.py collectstatic --no-input
fi

exec "$@"
