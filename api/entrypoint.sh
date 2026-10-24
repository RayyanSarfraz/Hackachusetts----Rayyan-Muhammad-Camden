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
# Guards: dev settings only, CSV must exist, and either store must be missing
# data: an empty Trial table, or fewer Chroma documents than trials (a previous
# seed that loaded Postgres but failed to index vectors). A complete index is
# never re-embedded, so restarts stay fast.
TRIALS_CSV="${TRIALS_CSV:-/data/source/trials/data.csv}"
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.development" ] && [ -f "$TRIALS_CSV" ]; then
    NEEDS_SEED="$(python -c "
import django, os
django.setup()
from apps.engine.models import Trial
from apps.engine.services.retriever import get_retriever
try:
    trials = Trial.objects.count()
    docs = get_retriever().document_count()
    print('yes' if trials == 0 or docs < trials else 'no')
except Exception:
    print('no')
" 2>/dev/null)"
    if [ "$NEEDS_SEED" = "yes" ]; then
        echo "Seeding clinical-trial data from $TRIALS_CSV (dev)..."
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
