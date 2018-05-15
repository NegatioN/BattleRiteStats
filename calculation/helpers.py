#!/usr/bin/env python3
# -*- coding: utf-8
import requests
import json
import pickle
import ntpath
import re
from bs4 import BeautifulSoup
from collections import defaultdict
from sqlalchemy import create_engine
import pandas as pd

def get_content(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
        return []

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

def colors_to_id_mapping(flattened_battlerites, cols, brite_name_method):
        name_lookup = {brite_name_method(x).lower(): x for x in list(flattened_battlerites.keys())}
        for c in cols:
                n = c['title'].lower()
                if n in name_lookup:
                        c['id'] = name_lookup[n]
        rev_col_lookup = {v['color']: k for k, v in battlerite_type_mapping.items()}
        out = {str(x['id']): rev_col_lookup[x['color']] for x in cols}
        return json.dumps(out)

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


def update_databases(master_team_dict):
    p_t = defaultdict(lambda: [])
    team_info = defaultdict(lambda: [])
    blaclisted_keys = ['users']
    for teamid,v in master_team_dict.items():
            teamid = int(teamid)
            for p in v['users']:
                    p_t['userid'].append(int(p))
                    p_t['teamid'].append(teamid)

            team_info['teamid'].append(teamid)
            for vs in v:
                    if vs not in blaclisted_keys:
                            team_info[vs].append(int(v[vs]))
    p_t_df = pd.DataFrame.from_dict(p_t)[['userid', 'teamid']]
    del p_t
    team_info_df = pd.DataFrame.from_dict(team_info)
    team_info_df['timee'] = team_info_df['time']
    team_info_df = team_info_df[['teamid', 'league', 'division', 'divrating', 'timee', 'wins', 'losses']]
    del team_info
    team_info_df.to_csv('db/tmp/t.csv', index=False)
    p_t_df.to_csv('db/tmp/pt.csv', index=False)

def get_player_ids():
    engine = create_engine('postgresql://psycopg:pass@localhost:5432/battleritebuilds')
    u = pd.read_sql_query('select distinct userid from playerteams NATURAL JOIN teams AS t WHERE t.league >= 5',con=engine)
    return u['userid'].values
