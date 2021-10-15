#!/bin/bash

set -e

db_uri="$1"

echo "$db_uri"

shift
cmd="$*"

until psql "${db_uri}" -c '\q'; do
  echo >&2 "Postgres is unavailable - sleeping"
  sleep 1
done

echo >&2 "Postgres is up - executing command"
exec $cmd
