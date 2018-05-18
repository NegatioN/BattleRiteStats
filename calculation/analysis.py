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


def load_locale(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = [x.strip().split('=') for x in f]
        return {x[0]: x[1] for x in data}

def load_characters(num):
    with open('assets/{}_gameplay.json'.format(num), 'rb') as gplay:
        gplay = gplay.read()
    return json.loads(gplay.decode('utf-8'))['characters']

def to_brites(characters):
    return {y['typeID']: y for x in characters for y in x['battlerites']}


c1, c2 = load_characters(0), load_characters(1)
b1, b2 = to_brites(c1), to_brites(c2)
l1, l2 = load_locale('assets/0_English.ini'), load_locale('assets/1_English.ini')

flattned_battlerites = b2
flattned_battlerites.update(b1)
locale_lookup = l2
locale_lookup.update(l1)  # This overwrites all existing keys with newer values
characters = c1
char_id_lookup = {x['typeID']: x for x in characters}

#Temporary hack
if 2018979014 in flattned_battlerites:
    flattned_battlerites[891919250] = flattned_battlerites[2018979014]


main_df = pd.read_csv('assets/character_df.csv')
match_df = pd.read_csv('assets/match_df.csv')

# Make each build hashably unique
main_df['build'] = main_df['build'].apply(lambda x: frozenset(x.split('|')))

def aggregate_lookup(main_df, match_df):
    round_dict = defaultdict((lambda: defaultdict(lambda: [])))
    for (matchid, userid), group in match_df.groupby(['matchid', 'userid']):
        round_dict[matchid][userid].extend(group.index.values)

    return main_df.apply(lambda x: round_dict[x['matchid']][x['userid']], axis=1)

main_df['round_lookup'] = aggregate_lookup(main_df, match_df)

exclude_columns = set(['matchid', 'userid', 'wonflag', 'round_num', 'team',
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
agg_cols.extend(['damage_ps', 'protection_ps', 'disables_ps', 'energy_ps'])


main_df['damage_ps'] = main_df['sum_damage'] / main_df['sum_time_alive']
main_df['protection_ps'] = main_df['sum_healing'] / main_df['sum_time_alive']
main_df['disables_ps'] = main_df['sum_disables'] / main_df['sum_time_alive']
main_df['energy_ps'] = main_df['sum_energy_gained'] / main_df['sum_time_alive']

grouped = main_df.groupby(['characterid', 'matchmode', 'build']).agg({k: np.mean for k in agg_cols})

build_counts = main_df.groupby(['characterid', 'matchmode'])['build'].value_counts().to_dict()
win_counts = main_df.groupby(['characterid', 'matchmode', 'build'])['wonflag'].value_counts().to_dict()
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

def hero_info(hero_id):
    return {'name': hero_name(hero_id),
            'title': hero_name(hero_id).replace(' ', '-').lower(),
            'icon': hero_icon(hero_id)}

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

def prep_output(num, prec=1, t=float):
    try:
        return '%.{}f'.format(prec) % t(num)
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
                 'winrate': prep_output(float(aggregations['win_num']) / float(aggregations['num']) * 100),
                 'damage': prep_output(aggregations['damage_ps']),
                 'protection': prep_output(aggregations['protection_ps']),
                 'disable': prep_output(aggregations['disables_ps']),
                 'energy': prep_output(aggregations['energy_ps'])
                 }
            cur_dict[character].append(b)


def sort_dict_array_by_key(dict_arr, key, rev=False):
    if rev:
        return [x for x in reversed(sorted(dict_arr, key=lambda k: k[key]))]
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

character_wins = defaultdict(lambda: defaultdict(lambda: 0))
for character, modes in character_dict.items():
    for mode, builds in modes.items():
        for build, aggregations in builds.items():
            character_wins[character][mode] += aggregations['win_num']

appearance_calculations = main_df.groupby(['characterid', 'matchmode']).size().to_dict().items()
appearance_summary = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))
for (h_id, mode), value in appearance_calculations:
    appearance_summary[h_id][mode]['num'] = int(value)
    appearance_summary[h_id][mode]['winrate'] = float(character_wins[h_id][mode]) / float(value)

named_appearance_summary = {hero_name(c): mode for c, mode in appearance_summary.items()}

compos = defaultdict(lambda: defaultdict(lambda: 0))
for (matchid, wonflag), group in main_df.groupby(['matchid', 'wonflag']):
    compset = frozenset([x for x in group['characterid']])
    compos[compset]['num'] += 1
    compos[compset]['wins'] += wonflag

tmp = [{'heros': [hero_info(z) for z in k], 'hero_names': [hero_name(z) for z in k],
        'wins': int(v['wins']), 'num': int(v['num']), 'winrate': float(v['wins'] / v['num'])}
       for k,v in compos.items()]
twos_compos = [x for x in tmp if len(x['heros']) == 2]
threes_compos = [x for x in tmp if len(x['heros']) == 3]

def hero_compos(hero_name, compo_list):
    return list(filter(lambda x: hero_name in x['hero_names'], compo_list))

def render_compos(hero_name, compo_list, num):
    h_comps = hero_compos(hero_name, compo_list)
    n = num if len(h_comps) > num else len(h_comps)
    return sort_dict_array_by_key(h_comps, 'num', rev=True)[:n]

def create_character_page_data(twos, threes, num_entries=10):
    chars = []
    all_entries = [x for x in zip(render_sort(twos, num_entries), render_sort(threes, num_entries))]
    for x in all_entries:
        name = x[0]['name']
        escaped_name = name.replace(' ', '-').lower()
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
            'compos': {'twos': render_compos(name, twos_compos, num_entries),
                       'threes': render_compos(name, threes_compos, num_entries)},
            'num': {'twos': named_appearance_summary[name]['QUICK2V2']['num'],
                    'threes': named_appearance_summary[name]['QUICK3V3']['num']},
            'winrate': {'twos': prep_output(named_appearance_summary[name]['QUICK2V2']['winrate'] * 100, prec=2),
                        'threes': prep_output(named_appearance_summary[name]['QUICK3V3']['winrate'] * 100, prec=2)}
        })
    return chars

character_page_data = create_character_page_data(twos, threes)

def mode_winrate_sorted(mode_string):
    arr = [{**hero_info(h_id),
            **mode[mode_string]} for h_id, mode in appearance_summary.items()]
    return sort_dict_array_by_key(arr, 'winrate', rev=True)

frontpage_data = sort_dict_array_by_key([hero_info(h_id) for h_id, mode in appearance_summary.items()], 'name')

master_d = {'frontpage': frontpage_data,
            'twos': mode_winrate_sorted('QUICK2V2'),
            'threes': mode_winrate_sorted('QUICK3V3'),
            'extra': {'time_generated': datetime.now().strftime('%d %B %Y'),
                      'num_matches': main_df['matchid'].nunique()}}

if len(twos) > 15 and len(threes) > 15:
    with open('assets/result.yml', 'w') as yaml_file:
        yaml.dump(master_d, yaml_file, default_flow_style=False)

for entry in character_page_data:
    char_name = entry['name']
    with open('assets/characters/{}.md'.format(char_name), 'w') as yaml_file:
        yaml.dump(entry, yaml_file, default_flow_style=False, explicit_start=True, explicit_end=True)