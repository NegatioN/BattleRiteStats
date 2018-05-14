#!/usr/bin/env bash

export PYTHONPATH="$(pwd)"
echo $PYTHONPATH
# database init
sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib
export DB_NAME="battleritebuilds"
sudo -u postgres createuser psycopg
sudo -u postgres createdb ${DB_NAME}
sudo -u postgres psql -d ${DB_NAME} -a -f db/databases.sql
mkdir db/tmp

mkdir assets
mkdir assets/characters
sudo pip3 install -r requirements.txt
python3 prepare_analysis_assets.py
BATTLERITE_API_KEY=${BATTLERITE_API_KEY} python3 calculate_builds.py
sudo -u postgres psql -d ${DB_NAME} -a -f db/update_base.sql

python3 analysis.py
python3 picture_assets.py

cp assets/result.yml ../_data/cdata.yml
cp assets/characters/* ../_characters
rm assets/characters/*
rm assets/result.yml
cd ..
git add .
git commit -m "Updated all champion data"
git pull --rebase
git push
#rm -rf assets
