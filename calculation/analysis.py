#!/usr/bin/env python3
# -*- coding: utf-8
import json
from datetime import datetime, timedelta
import yaml
from collections import defaultdict
import pandas as pd
import numpy as np
import re
from helpers import get_battlerite_type_mapping, get_battlerite_color_mapping

with open('assets/gameplay.json', 'rb') as gplay:
    gplay = gplay.read()

def load_locale(path):
    with open(path, 'r', encoding='utf-8') as f:

        data = [x.strip().split('=') for x in f]
        return {x[0]: x[1] for x in data}


locale_lookup = load_locale('assets/English.ini')
characters = json.loads(gplay.decode('utf-8'))['characters']
char_id_lookup = {x['typeID']: x for x in characters}
flattned_battlerites = {y['typeID']: y for x in characters for y in x['battlerites']}


main_df = pd.read_csv('assets/character_df.csv')
match_df = pd.read_csv('assets/match_df.csv')

# Make each build hashably unique
main_df['build'] = main_df['build'].apply(lambda x: frozenset(x.split(',')))

def aggregate_lookup(main_df, match_df):
    round_dict = defaultdict((lambda: defaultdict(lambda: [])))
    for (matchid, userid), group in match_df.groupby(['matchid', 'userid']):
        round_dict[matchid][userid].extend(group.index.values)

    return main_df.apply(lambda x: round_dict[x['matchid']][x['userid']], axis=1)

main_df['round_lookup'] = aggregate_lookup(main_df, match_df)

exclude_columns = set(['matchid', 'userid', 'wonFlag', 'round_num', 'team',
                       'healing_taken', 'damage_taken', 'disable_taken', 'energy_used'])
print(match_df.columns)
print('---------')
print(main_df.columns)
sum_cols = set(match_df.columns).symmetric_difference(exclude_columns)

def summer(rounds, col):
    return match_df.iloc[rounds][col].agg('sum')

def averager(rounds, col):
    return match_df.iloc[rounds][col].agg('mean')

for col in sum_cols:
    main_df["sum_" + col] = main_df.apply(lambda x: summer(x['round_lookup'], col), axis=1)
    main_df["mean_" + col] = main_df.apply(lambda x: averager(x['round_lookup'], col), axis=1)
    print('Processing match data for column={}'.format(col))

agg_cols = ['{}_{}'.format(y, x) for x in sum_cols for y in ['sum', 'mean']]
agg_cols.extend(['damage_ps', 'protection_ps', 'disable_ps', 'energy_ps'])


main_df['damage_ps'] = main_df['sum_damage'] / main_df['sum_time_alive']
main_df['protection_ps'] = main_df['sum_healing'] / main_df['sum_time_alive']
main_df['disable_ps'] = main_df['sum_disable'] / main_df['sum_time_alive']
main_df['energy_ps'] = main_df['sum_energy_gained'] / main_df['sum_time_alive']

grouped = main_df.groupby(['character', 'matchMode', 'build']).agg({k: np.mean for k in agg_cols})

build_counts = main_df.groupby(['character', 'matchMode'])['build'].value_counts().to_dict()
win_counts = main_df.groupby(['character', 'matchMode', 'build'])['wonFlag'].value_counts().to_dict()
character_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0))))
for aggregation, entry in grouped.items():
    for (character, mode, build), value in entry.items():
        character_dict[character][mode][build][aggregation] = value
        character_dict[character][mode][build]['num'] = build_counts[(character, mode, build)]
        try:
            character_dict[character][mode][build]['win_num'] = win_counts[(character, mode, build, 1)]
        except:
            character_dict[character][mode][build]['win_num'] = 0



### Rendering methods
def hero_name(hero_id):
    return locale_lookup[char_id_lookup[hero_id]['name']]

def hero_description(hero_id):
    return locale_lookup[char_id_lookup[hero_id]['description']]

def hero_title(hero_id):
    return locale_lookup[char_id_lookup[hero_id]['title']]

def hero_icon(hero_id):
    return char_id_lookup[hero_id]['wideIcon']

def brite_icon(battlerite_id):
    return flattned_battlerites[battlerite_id]['icon']

def brite_name(battlerite_id):
    return locale_lookup[flattned_battlerites[battlerite_id]['name']]

def brite_description(battlerite_id):
    brite = flattned_battlerites[battlerite_id]
    description = locale_lookup[brite['description']]
    vals = {x['Name'].lower(): x['Value'] for x in brite['tooltipData']}
    description = re.sub('{\d+}|{-}', '', description)
    return description.format(**vals)

color_lookup = get_battlerite_color_mapping()
type_lookup = get_battlerite_type_mapping()

twos = defaultdict(lambda: [])
threes = defaultdict(lambda: [])

def prep_output(num, t=int):
    try:
        a = t(num)
        return "{0:.1f}".format(a)
    except:
        return 0

for character, modes in character_dict.items():
    for mode, builds in modes.items():
        if '3' in mode:
            cur_dict = threes
        else:
            cur_dict = twos
        for build, aggregations in builds.items():
            time_alive_data = datetime.today() + timedelta(seconds=int(aggregations['sum_time_alive']))
            b = {'skills': [{'name': brite_name(int(x)),
                             'icon': brite_icon(int(x)),
                             'description': brite_description(int(x)),
                             'color': color_lookup[str(x)],
                             'type': type_lookup[str(x)]
                             }
                            for x in build],
                 'num': int(aggregations['num']),
                 'winrate': prep_output(float(aggregations['win_num']) / float(aggregations['num']) * 100, t=float),
                 'damage': prep_output(aggregations['damage_ps'], t=float),
                 'protection': prep_output(aggregations['protection_ps'], t=float),
                 'disable': prep_output(aggregations['disable_ps'], t=float),
                 'energy': prep_output(aggregations['energy_ps'], t=float)
                 }
            cur_dict[character].append(b)


def sort_dict_array_by_key(dict_arr, key, rev=False):
    if rev:
        return reversed(sorted(dict_arr, key=lambda k: k[key]))
    else:
        return sorted(dict_arr, key=lambda k: k[key])

def sort_builds(builds, limit):
    def sort_alphabetically(stats):
        stats['skills'] = sort_dict_array_by_key(stats['skills'], 'name')
        return stats
    n = len(builds) if limit > len(builds) else limit
    return [sort_alphabetically(x) for x in [z for z in sort_dict_array_by_key(builds, 'num', rev=True)][:n]]

def render_sort(mode_dict, limit):
    rendered_mode = [{'name': hero_name(hero_id),
                      'title': hero_name(hero_id).replace(' ', '-').lower(),
                      'description': hero_description(hero_id),
                      'icon': hero_icon(hero_id),
                      'builds': sort_builds(mode_dict[hero_id], limit)}
                     for hero_id in mode_dict.keys()]
    return sort_dict_array_by_key(rendered_mode, 'name')

master_d = {'twos': render_sort(twos, 3),
            'threes': render_sort(threes, 3),
            'extra': {'time_generated': datetime.now().strftime('%d %B %Y'),
                      'num_matches': main_df['matchid'].nunique()}}


appearance_summary = {hero_name(h_id): int(v) for h_id, v in main_df.groupby('character').size().to_dict().items()}
win_agg = main_df.groupby('character')['wonFlag'].agg('sum')
winrate_summary = {x[0]: int(float(x[1]) / float(appearance_summary[x[0]]) * 100)
                   for x in zip([hero_name(z) for z in win_agg.index], win_agg)}

def create_character_page_data(twos, threes):
    chars = []
    all_entries = [x for x in zip(render_sort(twos, 5), render_sort(threes, 5))]
    for x in all_entries:
        name = x[0]['name']
        escaped_name = name.replace(' ', '_').lower()
        chars.append({
            'layout': 'character',
            'title': name,
            'name': escaped_name,
            'description': x[0]['description'],
            'icon': x[0]['icon'],
            'url': "characters/" + escaped_name + ".html",
            'builds':
                {'twos': x[0]['builds'],
                 'threes': x[1]['builds']
                 },
            'num': appearance_summary[name],
            'winrate': winrate_summary[name]
        })
    return chars

character_page_data = create_character_page_data(twos, threes)


if len(twos) > 15 and len(threes) > 15:
    with open('assets/result.yml', 'w') as yaml_file:
        yaml.dump(master_d, yaml_file, default_flow_style=False)

for entry in character_page_data:
    char_name = entry['name']
    with open('assets/characters/{}.md'.format(char_name), 'w') as yaml_file:
        yaml.dump(entry, yaml_file, default_flow_style=False, explicit_start=True, explicit_end=True)