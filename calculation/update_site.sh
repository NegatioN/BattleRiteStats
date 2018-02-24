#!/usr/bin/env bash

mkdir assets
sudo pip install -r requirements.txt
python prepare_assets.py
python calculate_builds.py
python analysis.py

cp assets/result.yml ../_data/cdata.yml
rm -rf assets

#TODO copy data-file to ../_data/cdata.yml
#TODO git commit
#TODO git push