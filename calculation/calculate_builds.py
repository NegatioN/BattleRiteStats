#!/usr/bin/env python3
# -*- coding: utf-8
import requests
from urllib.parse import quote
import os
from ratelimiter import RateLimiter
from datetime import timedelta, datetime
from copy import deepcopy

from helpers import get_user_ids
from telem_cache import TelemetryCache
from collections import defaultdict
from furrycorn.location import mk_origin, mk_path, mk_query, to_url
import pandas as pd

api_key = os.environ.get('BATTLERITE_API_KEY')
print('Api key is set={}'.format("Yes" if api_key else "No"))
origin = mk_origin('https', 'api.dc01.gamelockerapp.com', '/shards/global')
headers = {'Accept': 'application/vnd.api+json',
           'Accept-Encoding': 'gzip',
           'Authorization': 'Bearer {0}'.format(api_key)}
rate_limiter = RateLimiter(max_calls=100, period=61)

telem_cache = TelemetryCache()

def jsonify_datetime(d):
    return d.strftime('%Y-%m-%dT%H:00:00Z')

#Last seven days of replays
last_patch = datetime(year=2018, month=4, day=26, hour=0)
seven_days_ago = datetime.now() - timedelta(days=7)
if last_patch < datetime.now() and last_patch > seven_days_ago:
    created_after_date = jsonify_datetime(last_patch)
    created_ad = last_patch
else:
    created_after_date = jsonify_datetime(seven_days_ago)
    created_ad = seven_days_ago

print('Getting matches from {} to now'.format(created_after_date))

main_df = pd.DataFrame(columns=['matchid', 'userid', 'character', 'build', 'matchMode'])
match_df = pd.DataFrame(columns=['matchid', 'round_num', 'round_duration', 'userid', 'team',
                                 'kills', 'score', 'deaths', 'damage', 'healing', 'disable',
                                 'energy_used', 'energy_gained', 'damage_taken','healing_taken',
                                 'disable_taken', 'wonFlag', 'time_alive'])
base_collector_dict = {x: [] for x in main_df.columns}
base_match_collector_dict = {x: [] for x in match_df.columns}

def find_match_type(telemetry_entry):
    for cursor in telemetry_entry:
        try:
            return cursor['dataObject']['serverType']
        except:
            pass
    return ""

def parse_sporadic_character_data(telemetry_entry):
    match_characters = defaultdict(lambda: defaultdict(lambda: set()))
    for cursor in telemetry_entry:
        try:
            brite = cursor['dataObject']['battleriteType']
            userid = cursor['dataObject']['userID']
            character = cursor['dataObject']['character']
            match_characters[character][userid].add(brite)
        except:
            pass
    return match_characters

def find_match_id(telemetry_entry):
    for cursor in telemetry_entry:
        try:
            return cursor['dataObject']['matchID']
        except:
            pass
    return "NoMatchId"

def parse_telemetry(telemetry_entry):
    match_mode = find_match_type(telemetry_entry)
    match_id = find_match_id(telemetry_entry)
    match_characters = parse_sporadic_character_data(telemetry_entry)
    collector_dict = deepcopy(base_collector_dict)
    add = lambda s, e: collector_dict[s].append(e)
    for character, d in match_characters.items():
        for userid, build in d.items():
            add('matchid', match_id)
            add('userid', userid)
            add('character', character)
            add('build', ",".join([str(x) for x in build]))
            add('matchMode', match_mode)
    return pd.DataFrame.from_dict(data=collector_dict)[main_df.columns]


def parse_round_statistics(telem_entry):
    collector_dict = deepcopy(base_match_collector_dict)
    add = lambda s, e: collector_dict[s].append(e)
    for cursor in telem_entry:
        if cursor['type'] == 'Structures.RoundFinishedEvent':
            data = cursor['dataObject']
            matchid = data['matchID']
            round_num = data['round']
            round_duration = data['roundLength']
            #round_start = data['time']
            winning_team = data['winningTeam']
            player_per_team = len(data['playerStats']) / 2
            for i, player in enumerate(data['playerStats']):
                team_num = 1 if i < player_per_team else 2
                add('matchid', matchid)
                add('round_num', round_num)
                add('round_duration', round_duration)
                add('userid', player['userID'])
                add('team', team_num)
                add('kills', player['kills'])
                add('deaths', player['deaths'])
                add('score', player['score'])
                add('damage', player['damageDone'])
                add('healing', player['healingDone'])
                add('disable', player['disablesDone'])
                add('wonFlag', 1 if team_num == winning_team else 0)
                add('time_alive', player['timeAlive'])
                add('damage_taken', player['damageReceived'])
                add('healing_taken', player['healingReceived'])
                add('disable_taken', player['disablesReceived'])
                add('energy_used', player['energyUsed'])
                add('energy_gained', player['energyGained'])

    return pd.DataFrame.from_dict(data=collector_dict)[match_df.columns]


def construct_url(player_id, ranked=True):
    query_params = {'filter[playerIds]': quote(player_id), 'filter[createdAt-start]': created_after_date}
    if ranked:
        query_params['filter[rankingType]'] = 'RANKED'
        query_params['filter[serverType]'] = 'QUICK2V2,QUICK3v3'
    return to_url(origin, mk_path('/matches'), mk_query(query_params))

def parse_list_node(all_data_nodes, typ):
    return set([y['id'] for x in all_data_nodes for y in x['relationships'][typ]['data']])

def get_player_telemetry(player_id):
    telemetry_links = set()
    url = construct_url(player_id)
    while url:
        with rate_limiter:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                content = response.json()
                all_data_nodes = content['data']
                match_ids = parse_list_node(all_data_nodes, 'assets')

                for node in content['included']:
                    if 'id' in node and node['id'] in match_ids:
                        telemetry_links.add(node['attributes']['URL'])

                url = content['links']['next'] if 'next' in content['links'] else None
            else:
                url = None

    print('found {} matches for player={}'.format(len(telemetry_links), player_id))
    return telemetry_links


def get_telemetry_data(url):
    telemetry_entry = telem_cache.get_cached_telemetry(url)
    if not telemetry_entry:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                telemetry_entry = resp.json()
                telem_cache.cache_telemetry(url, telemetry_entry)
        except:
            print('something bad happened')
            telemetry_entry = []

    return telemetry_entry


if __name__ == "__main__":
    player_ids = get_user_ids()
    print('Number of users to process: {}'.format(len(player_ids)))
    all_telemetries = set()
    telem_cache.clean_cache(created_ad)

    # For some reason this function returns duplicates ¯\_(ツ)_/¯
    for player_id in player_ids:
        telems = get_player_telemetry(player_id)
        all_telemetries = all_telemetries.union(telems)

    print('{} match-telemetries'.format(len(all_telemetries)))

    for telem_url in all_telemetries:
        print('processing {}'.format(telem_url))
        telemetry_entry = get_telemetry_data(telem_url)
        m_df = parse_round_statistics(telemetry_entry)
        c_df = parse_telemetry(telemetry_entry)
        main_df = pd.concat([main_df, c_df]).reset_index().drop('index', 1)
        match_df = pd.concat([match_df, m_df]).reset_index().drop('index', 1)


    def aggregate_wins(main_df, match_df):
        # I dont like how this is solved... there must be some better way to access grouped queries.
        win_dict = defaultdict((lambda: defaultdict(lambda: 0)))
        for (matchid, userid), group in match_df.groupby(['matchid', 'userid']):
            win_dict[matchid][userid] = group['wonFlag'].sum()

        #TODO possible discrepency with leaver matches
        threshold = lambda x: 3  # Change if there are different win-conditions
        won_round = lambda x, mr_won: 1 if mr_won == threshold(x) else 0

        main_df['wonFlag'] = main_df.apply(lambda x: won_round(x, win_dict[x['matchid']][x['userid']]), axis=1)

    aggregate_wins(main_df, match_df)

    main_df.to_csv('assets/character_df.csv', index=False)
    match_df.to_csv('assets/match_df.csv', index=False)

print('Cache hits: {}'.format(telem_cache.cache_hits))
print('Added to cache: {}'.format(telem_cache.added_to_cache))
