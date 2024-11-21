#!/bin/bash

set -e

DB_HOST=${DB_HOST:-localhost}
ADB_PORT=${ADB_PORT:-55555}
DB_USER=${DB_USER:-admin}
DB_PASS=${DB_PASS:-admin}

echo "Starting server, setting config to $DB_HOST on $ADB_PORT"
cd /aperturedb

aperturedb -cfg config.json &
pid=$!

echo adb config create default --host $DB_HOST --port $ADB_PORT --username $DB_USER --password "$DB_PASS" --no-interactive
adb config create default --overwrite --host $DB_HOST --port $ADB_PORT --username $DB_USER --password "$DB_PASS" --no-interactive


sleep 5
cd /
bash add_users.sh

wait
