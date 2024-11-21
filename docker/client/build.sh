#!/bin/bash

base=$(dirname $(realpath ${0}))/../..

rm -rf app
mkdir app
cp "${base}"/*.csv app
cp "${base}"/*.py app
cp "${base}"/test_files.sh app

docker build -t langsafe-client .
