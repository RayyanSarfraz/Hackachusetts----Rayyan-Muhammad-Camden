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

if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
    python manage.py collectstatic --no-input
fi

exec "$@"
