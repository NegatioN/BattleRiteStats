#!/usr/bin/env python3
# -*- coding: utf-8
import requests
import json
import pickle
from collections import defaultdict
import ntpath
import re
from bs4 import BeautifulSoup
from collections import defaultdict

def chunks(arr, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(arr), n):
            yield arr[i:i + n]


def get_content(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))['data']
    else:
        return []

def parse_list_node(all_data_nodes, typ):
    return set([y['id'] for x in all_data_nodes for y in x['relationships'][typ]['data']])

def get_telemtry(url, headers):
    response = requests.get(url, headers=headers)
    telemetry_urls = set()
    if response.status_code == 200:
        content = json.loads(response.content.decode('utf-8'))
        all_data_nodes = content['data']
        match_ids = parse_list_node(all_data_nodes, 'assets')

        for node in content['included']:
            if 'id' in node and node['id'] in match_ids:
                telemetry_urls.add(node['attributes']['URL'])

        return telemetry_urls
    else:
        return set()

def default_to_regular(d):
    if isinstance(d, defaultdict):
        d = {k: default_to_regular(v) for k, v in d.items()}
    return d

def pickle_info(build_info, filename):
    with open('assets/{}'.format(filename), 'wb+') as f:
        f.write(pickle.dumps(default_to_regular(build_info)))

def load_pickle(filename):
    with open('assets/{}'.format(filename), 'rb') as f:
        return pickle.loads(f.read())

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

'''Kinda manual method for getting color-scheme of character skills for now. Just run for all heros'''
def bootstrap_character_colors(hero_name):
    cont = requests.get('https://battlerite.gamepedia.com/{}/Battlerites'.format(hero_name.replace(' ', '_'))).text
    bs = BeautifulSoup(cont, "html.parser")
    stuff = bs.find_all('div', {'class': 'battlerite'})
    char_colors = []
    for s in stuff:
        title = s.find('div', {'class': 'battlerite--title'}).p.text
        color_alt = s.find('div', {'class': 'battlerite--art'}).img['alt']
        color = re.split('\s', color_alt)[-1].split('.')[0].lower()
        char_colors.append({'title': title, 'color': color})
    return char_colors

battlerite_type_mapping = {1: {'color': 'red', 'type': 'offense'},
                           2: {'color': 'yellow', 'type': 'mobility'},
                           3: {'color': 'blue', 'type': 'utility'},
                           4: {'color': 'green', 'type': 'survival'},
                           5: {'color': 'pink', 'type': 'control'},
                           6: {'color': 'teal', 'type': 'support'},
                           7: {'color': 'grey', 'type': 'mixed'}}

def get_battlerite_color_mapping():
    with open('battlerites_type_mappings.json', 'r') as f:
        defined_mappings = json.load(f)
        color_mappings = defaultdict(lambda: battlerite_type_mapping[7]['color'])
        for k, v in defined_mappings.items():
            color_mappings[k] = battlerite_type_mapping[v]['color']
        return color_mappings


def get_battlerite_type_mapping():
    with open('battlerites_type_mappings.json', 'r') as f:
        defined_mappings = json.load(f)
        type_mappings = defaultdict(lambda: battlerite_type_mapping[7]['type'])
        for k, v in defined_mappings.items():
            type_mappings[k] = battlerite_type_mapping[v]['type']
        return type_mappings
