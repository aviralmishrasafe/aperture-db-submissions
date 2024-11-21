#!/bin/bash
# remove old configs
rm -rf /root/.config/aperturedb

adb config create default --host $ADB_HOST --port $ADB_PORT --username $ADB_USER --password "$ADB_PASS" --no-interactive --active
cd app && bash ./test_files.sh
