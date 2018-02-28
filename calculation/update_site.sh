#!/usr/bin/env bash
git pull
git checkout gh-pages
export PYTHONPATH="$(pwd)"
echo $PYTHONPATH
mkdir assets
sudo pip3 install -r requirements.txt
python3 prepare_analysis_assets.py
BATTLERITE_API_KEY=${BATTLERITE_API_KEY} python3 calculate_builds.py
python3 analysis.py
python3 picture_assets.py

cp assets/result.yml ../_data/cdata.yml
rm assets/result.yml
cd ..
git add .
git commit -m "Updated all champion data"
git push
#rm -rf assets
