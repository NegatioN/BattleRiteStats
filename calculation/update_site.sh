#!/usr/bin/env bash
export PYTHONPATH="$(pwd)"
echo $PYTHONPATH
mkdir assets
sudo pip3 install -r requirements.txt
python3 prepare_assets.py
BATTLERITE_API_KEY=${BATTLERITE_API_KEY} python3 calculate_builds.py
python3 analysis.py

cp assets/result.yml ../_data/cdata.yml
#rm -rf assets
#cd ..
#git add .
#git commit -m "Updated all champion data"
#git push