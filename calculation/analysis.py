#!/usr/bin/env python3
# -*- coding: utf-8
from helpers import load_pickle, chunks, get_content
from furrycorn.location import mk_origin, mk_path, mk_query, to_url
import json
from ratelimiter import RateLimiter
from datetime import datetime
import yaml
import operator
from collections import defaultdict
'''
origin = mk_origin('https', 'api.dc01.gamelockerapp.com', '/shards/global')
headers = {'Accept': 'application/vnd.api+json',
           'Authorization': 'Bearer {0}'.format(api_key)}
rate_limiter = RateLimiter(max_calls=10, period=61)


def get_player(player_ids):
    if type(player_ids) != list:
        player_ids = [player_ids]
    url = to_url(origin, mk_path('/players'), mk_query({'filter[playerIds]': ','.join(player_ids)}))
    with rate_limiter:
        return get_content(url, headers)
        

def make_player_lookup(player_ids):
    p_data = []
    for c in chunks(player_ids, 5):
        p_data.append(get_player(c))
    return {y['id']: y['attributes']['name'] for x in p_data for y in x}
    '''

with open('assets/gameplay.json', 'rb') as gplay:
    gplay = gplay.read()

def load_locale(path):
    with open(path, 'r', encoding='utf-8') as f:
        
        data = [x.strip().split('=') for x in f]
        return {x[0]: x[1] for x in data}


locale_lookup = load_locale('assets/English.ini')
characters = json.loads(gplay.decode('utf-8'))['characters']
char_id_lookup = {x['typeID']: i for i,x in enumerate(characters)}


player_data = load_pickle('player_builds.p')
character_builds = load_pickle('character_builds.p')
extras = load_pickle('extras.p')
#player_lookup = make_player_lookup([str(x) for x in player_data.keys()])

def sorted_by_count(x):
    return reversed(sorted(x.items(), key=operator.itemgetter(1)))

def sorted_by_countarr(x):
    return reversed(sorted(x, key=lambda k: k['num']))

def hero_id_to_name(hero_id):
    return locale_lookup[characters[char_id_lookup[hero_id]]['name']]

def make_brite_names(character_data, brite_lookup, brites):
    brite_names = []
    for b in brites:
        entry = {}
        try:
            entry['name'] = locale_lookup[character_data['battlerites'][brite_lookup[b]]['name']]
            entry['icon'] = character_data['battlerites'][brite_lookup[b]]['icon']
        except:
            entry['name'] = "VERY UNKNOWN"
            entry['icon'] = "VERY UNKNOWN"
        brite_names.append(entry)
    return brite_names

def dictify_character_builds(brite_lookup, character_data, character_dict):
    builds = []
    for build, count in sorted_by_count(character_dict):
        b = {'skills': make_brite_names(character_data, brite_lookup, build),
             'num': count}
        builds.append(b)
    return builds

twos_builds = []
threes_builds = []

for mode, mode_dict in character_builds.items():
    d = twos_builds if '2' in mode else threes_builds
    #Find most popular builds for each hero
    for hero_id, build_dict in mode_dict.items():
        character_data = characters[char_id_lookup[hero_id]]
        name = locale_lookup[character_data['name']]
        brite_lookup = {x['typeID']: i for i, x in enumerate(character_data['battlerites'])}
        c_dict = {'builds': dictify_character_builds(brite_lookup, character_data, build_dict),
                  'name': name}
        d.append(c_dict)

    print('Most popular heroes in {}:\n'.format(mode))
    #Find most popular heroes
    appearance_summary = defaultdict(lambda: 0)
    for hero_id, build_dict in mode_dict.items():
        name = hero_id_to_name(hero_id)
        for build, count in build_dict.items():
            appearance_summary[name] += count

    print([x for x in sorted_by_count(appearance_summary)])

def sort_array_dicts_by_key(dict_arr, key):
    return sorted(dict_arr, key=lambda k: k[key])


def sort_skills_alphabetically(builds_array):
    for build in builds_array:
        build['skills'] = sort_array_dicts_by_key(build['skills'], 'name')

    return builds_array

def num_builds_subset(character_build_array, num=3):
    limited_subset = []
    for x in character_build_array:
        n = len(x['builds']) if num > len(x['builds']) else num
        builds = [x for x in sorted_by_countarr(x['builds'])][:n]
        limited_subset.append({'name': x['name'], 'builds': sort_skills_alphabetically(builds)})
    return limited_subset


prepare_dict = lambda d, num: sort_array_dicts_by_key(num_builds_subset(d, num), 'name')

master_d = {'twos': prepare_dict(twos_builds, 3),
            'threes': prepare_dict(threes_builds, 3),
            'extra': {'time_generated': datetime.now().strftime('%d %B %Y'),
                      'num_matches': extras['num_matches']}}

def create_character_page_data(twos, threes):
    chars = []
    all_entries = [x for x in zip(prepare_dict(twos, 5), prepare_dict(threes, 5))]
    for x in all_entries:
        name = x[0]['name']
        chars.append({
            'layout': 'character',
            'title': name,
            'name': name.replace(' ', '_').lower(),
            'url': "characters/" + name.replace(' ', '_').lower() + ".html",
            'builds':
                {'twos': x[0]['builds'],
                'threes': x[1]['builds']
                 },
            'num': appearance_summary[name]
        })
    return chars

character_page_data = create_character_page_data(twos_builds, threes_builds)


if len(twos_builds) > 15 and len(threes_builds) > 15:
    with open('assets/result.yml', 'w') as yaml_file:
        yaml.dump(master_d, yaml_file, default_flow_style=False)

for entry in character_page_data:
    char_name = entry['name']
    with open('assets/characters/{}.md'.format(char_name), 'w') as yaml_file:
        yaml.dump(entry, yaml_file, default_flow_style=False, explicit_start=True, explicit_end=True)
