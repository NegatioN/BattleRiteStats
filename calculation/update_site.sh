#!/usr/bin/env bash

if [[ $(uname -a) = *"armv7l"* ]]; then
  echo "Running raspberry pi, installng PIL"
  sudo apt-get update && sudo apt-get install -y python-imaging python3-pil.imagetk
fi

export PYTHONPATH="$(pwd)"
echo $PYTHONPATH
mkdir assets
mkdir assets/characters
sudo pip3 install -r requirements.txt
python3 prepare_analysis_assets.py
BATTLERITE_API_KEY=${BATTLERITE_API_KEY} python3 calculate_builds.py
python3 analysis.py
python3 picture_assets.py

cp assets/result.yml ../_data/cdata.yml
cp assets/characters/* ../_characters
rm assets/characters/*
rm assets/result.yml
cd ..
git add .
git commit -m "Updated all champion data"
git push
#rm -rf assets
