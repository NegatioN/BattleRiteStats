#!/usr/bin/env python3
# -*- coding: utf-8
import os
import json
from helpers import path_leaf
from PIL import Image
import yaml

def base(p):
    return os.path.splitext(p)[0]

'''Takes in image-names with extension, and converts to png'''
def convert_to_png(img_name, in_path, out_path):
    img = Image.open(os.path.join(in_path, img_name))
    img.save(os.path.join(out_path, base(img_name) + ".png"))

def get_unique_brite_icon(characters):
    unique_assets = set()
    for character in characters:
        for bs in character['builds']:
            for vals in bs['skills']:
                unique_assets.add(vals['icon'])
    return unique_assets

with open('assets/gameplay.json', 'rb') as gplay:
    gplay = gplay.read()

characters = json.loads(gplay.decode('utf-8'))['characters']
flattned_battlerites = {y['typeID']: y for x in characters for y in x['battlerites']}


with open('assets/result.yml', 'r', encoding='utf-8') as f:
    result_data = yaml.load(f)

pic_assets_path = 'assets/brite_assets/mappings/assets'

webpage_to_path = '../assets/img'

skill_icons = set()
for brite in flattned_battlerites:
    d = flattned_battlerites[brite]
    skill_icons.add(d['icon'])

char_icons = set()
for c in characters:
    char_icons.add(c['icon'])
    char_icons.add(c['wideIcon'])

unique_assets = skill_icons.union(char_icons)

existing_image_resources = [base(x) for x in os.listdir(webpage_to_path)]

for x in os.listdir(pic_assets_path):
    resource_name = base(x)
    if resource_name in unique_assets and resource_name not in existing_image_resources:
        convert_to_png(path_leaf(x), pic_assets_path, webpage_to_path)