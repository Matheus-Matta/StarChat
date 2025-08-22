#!/bin/sh
set -e

echo "→ Aguardando Postgres em $DB_HOST:$DB_PORT…"
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
  sleep 0.5
done
echo "→ PostgreSQL pronto!"

python manage.py makemigrations --no-input
python manage.py migrate --no-input
find static -type f -name "*.min.js" -print0 | xargs -0 sed -i '/sourceMappingURL=.*\.map/d'
python manage.py collectstatic --no-input --clear

exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000
