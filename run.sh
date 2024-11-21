#!/bin/bash
for d in $(ls docker); do
    (cd docker/"$d" && bash build.sh )
done
echo "Images built, running compose, Ctrl-C to exit."
docker compose up
