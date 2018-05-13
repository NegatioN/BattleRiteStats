#!/usr/bin/env python3
# -*- coding: utf-8
import requests
from urllib.parse import quote
import os
from ratelimiter import RateLimiter
from datetime import timedelta, datetime
from copy import deepcopy

from helpers import get_user_ids, update_databases
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

date_format = '%Y-%m-%dT%H:%M:%SZ'
def jsonify_datetime(d): return d.strftime(date_format)

def timestampify_jsontime(j): return datetime.strptime(j, date_format).timestamp()

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

main_df = pd.DataFrame(columns=['matchid', 'userid', 'character', 'build', 'matchMode',
                                'patchVersion', 'mapID', 'time', 'rankingType', 'external_matchid'])
match_df = pd.DataFrame(columns=['matchid', 'round_num', 'round_duration', 'userid', 'team',
                                 'kills', 'score', 'deaths', 'damage', 'healing', 'disable',
                                 'energy_used', 'energy_gained', 'damage_taken','healing_taken',
                                 'disable_taken', 'wonFlag', 'time_alive'])
base_collector_dict = {x: [] for x in main_df.columns}
base_match_collector_dict = {x: [] for x in match_df.columns}

def compile_match_battlerites(telem_d):
    match_characters = defaultdict(lambda: defaultdict(lambda: set()))
    for event in telem_d['Structures.BattleritePickEvent']:
        brite = event['battleriteType']
        userid = event['userID']
        character = event['character']
        match_characters[character][userid].add(brite)

    return match_characters

def parse_telemetry(telem_d):
    match_characters = compile_match_battlerites(telem_d)
    collector_dict = deepcopy(base_collector_dict)
    add = lambda s, e: collector_dict[s].append(e)
    for character, d in match_characters.items():
        for userid, build in d.items():
            add('matchMode', telem_d['serverType'])
            add('matchid', telem_d['matchID'])
            add('external_matchid', telem_d['external_matchid'])
            add('patchVersion', telem_d['patchVersion'])
            add('mapID', telem_d['map'])
            add('time', telem_d['time'])
            add('rankingType', telem_d['rankingType'])
            add('userid', userid)
            add('character', character)
            add('build', ",".join([str(x) for x in build]))
    return pd.DataFrame.from_dict(data=collector_dict)[main_df.columns]

def parse_round_statistics(telem_d):
    collector_dict = deepcopy(base_match_collector_dict)
    add = lambda s, e: collector_dict[s].append(e)
    for data in telem_d['Structures.RoundFinishedEvent']:
        matchid = data['matchID']
        round_num = data['round']
        round_duration = data['roundLength']
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


def get_player_telemetry(player_id):
    telemetry_links = {}
    url = construct_url(player_id)
    while url:
        with rate_limiter:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                content = response.json()
                match_data = {}
                for node in content['data']:
                    match_id = node['relationships']['assets']['data'][0]['id']
                    match_data[match_id] = {'external_matchid': match_id,
                                            'patchVersion': (node['attributes']['patchVersion']),
                                            'map': (node['attributes']['stats']['mapID']),
                                            'serverType': (node['attributes']['tags']['serverType']),
                                            'time': (timestampify_jsontime(node['attributes']['createdAt'])),
                                            'rankingType': (node['attributes']['tags']['rankingType'])}

                match_ids = list(match_data.keys())
                for node in content['included']:
                    if 'id' in node and node['id'] in match_ids:
                        mid = node['id']
                        telemetry_links[node['attributes']['URL']] = {**match_data[mid]}

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
            print('something bad happened with entry: {}'.format(url))
            telemetry_entry = []
    telem_d = defaultdict(lambda: [])
    for c in telemetry_entry:
        data = c['dataObject']
        telem_d[c['type']].append(data)
        if 'matchID' in data:
            telem_d['matchID'] = data['matchID']

    return telem_d

def get_team_info(telem_d):
    t_p_dict = defaultdict(lambda: defaultdict(lambda: 0))
    for event in telem_d['com.stunlock.battlerite.team.TeamUpdateEvent']:
        player_ids = [x for x in event['userIDs'] if x != 0]

        team_id = event['teamID']
        t_p_dict[team_id]['league'] = event['league']
        t_p_dict[team_id]['division'] = event['division']
        t_p_dict[team_id]['divrating'] = event['divisionRating']
        t_p_dict[team_id]['time'] = event['time']
        t_p_dict[team_id]['wins'] = event['wins']
        t_p_dict[team_id]['losses'] = event['losses']
        t_p_dict[team_id]['users'] = player_ids
    return t_p_dict



if __name__ == "__main__":
    player_ids = get_user_ids()
    print('Number of users to process: {}'.format(len(player_ids)))
    all_telemetries = {}
    telem_cache.clean_cache(created_ad)
    master_team_dict = defaultdict(lambda: defaultdict(lambda: 0))

    for player_id in player_ids:
        telems = get_player_telemetry(player_id)
        all_telemetries.update(telems)

    print('{} match-telemetries'.format(len(all_telemetries)))

    for telem_url, data in all_telemetries.items():
        try:
            telem_dd = get_telemetry_data(telem_url)
            telem_dd.update(data)
            m_df = parse_round_statistics(telem_dd)
            c_df = parse_telemetry(telem_dd)
            master_team_dict.update(get_team_info(telem_dd))
            main_df = pd.concat([main_df, c_df]).reset_index().drop('index', 1)
            match_df = pd.concat([match_df, m_df]).reset_index().drop('index', 1)
        except:
            print('Something went wrong processing {}'.format(telem_url))


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

    update_databases(master_team_dict=master_team_dict)

print('Cache hits: {}'.format(telem_cache.cache_hits))
print('Added to cache: {}'.format(telem_cache.added_to_cache))
