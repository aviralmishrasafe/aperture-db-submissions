#!/bin/bash
# sleep since we don't wait for db to come up first.
sleep 10
adb utils execute remove_all --force
# add all data to db.
python3 load.py
python3 check.py -o 9 github_secrets # is owner.
python3 check.py -a 9 github_secrets # can access [ not by group ]
python3 check.py -a 1 github_secrets # cannot access
python3 check.py  -a 12 github_secrets # can access by devs which includes sysadmins.
