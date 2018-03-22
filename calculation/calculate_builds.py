#!/usr/bin/env python3
# -*- coding: utf-8
import requests
from urllib.parse import quote
import json
from ratelimiter import RateLimiter
from datetime import timedelta, datetime
import os
from copy import deepcopy

from helpers import chunks, get_content,  get_telemtry
from telem_cache import cache_telemetry, get_cached_telemetry, clean_cache
from collections import defaultdict
from furrycorn.location import mk_origin, mk_path, mk_query, to_url
import pandas as pd

api_key = os.environ.get('BATTLERITE_API_KEY')
print('Api key is set={}'.format("Yes" if api_key else "No"))
origin = mk_origin('https', 'api.dc01.gamelockerapp.com', '/shards/global')
headers = {'Accept': 'application/vnd.api+json',
           'Accept-Encoding': 'gzip',
           'Authorization': 'Bearer {0}'.format(api_key)}
rate_limiter = RateLimiter(max_calls=50, period=61)

def jsonify_datetime(d):
    return d.strftime('%Y-%m-%dT%H:00:00Z')

#Last seven days of replays
last_patch = datetime(year=2018, month=3, day=8, hour=12)
seven_days_ago = datetime.now() - timedelta(days=7)
if last_patch < datetime.now() and last_patch > seven_days_ago:
    created_after_date = jsonify_datetime(last_patch)
    created_ad = last_patch
else:
    created_after_date = jsonify_datetime(seven_days_ago)
    created_ad = seven_days_ago

print('Getting matches from {} to now'.format(created_after_date))


def get_match_info(player_id, offset=0, ranked=True):
    query_params = {'filter[playerIds]': quote(player_id), 'page[offset]': offset, 'filter[createdAt-start]': created_after_date}
    if ranked:
        query_params['filter[rankingType]'] = 'RANKED'
        query_params['filter[serverType]'] = 'QUICK2V2,QUICK3v3'
    url = to_url(origin, mk_path('/matches'), mk_query(query_params))
    return get_telemtry(url, headers)

def get_player(player_names):
    if type(player_names) != list:
        player_names = [player_names]
    player_names = list(map(lambda n: quote(n), player_names))
    url = to_url(origin, mk_path('/players'), mk_query({'filter[playerNames]': player_names}))
    with rate_limiter:
        return get_content(url, headers)

main_df = pd.DataFrame(columns=['matchid', 'userid', 'character', 'build', 'matchMode'])
match_df = pd.DataFrame(columns=['matchid', 'round_num', 'round_duration', 'userid', 'team',
                                 'kills', 'score', 'deaths', 'damage', 'healing', 'disable',
                                 'energy_used', 'energy_gained', 'damage_taken','healing_taken',
                                 'disable_taken', 'wonFlag', 'time_alive'])
base_collector_dict = {x: [] for x in main_df.columns}
base_match_collector_dict = {x: [] for x in match_df.columns}

def get_player_ids(player_names):
    p_data = []
    for c in chunks(player_names, 5):
        p_data.append(get_player(c))
    return [y['id'] for x in p_data for y in x]

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


def get_player_telemetry(player_id, max_count=20):
    count, step = 0, 5
    telemetry_links = []
    while count < max_count:
        with rate_limiter:
            try:
                t_links = get_match_info(player_id, offset=step * count)
                if len(t_links) > 0:
                    telemetry_links.append(t_links)
                    count += 1
                else:
                    print('Most likely no more pages of matches which meet requirements for player={}'.format(player_id))
                    break
            except:
                print('Most likely no more pages of matches which meet requirements for player={}'.format(player_id))
                break

    telemetry_links = [y for x in telemetry_links for y in x]
    print('found {} matches for player={}'.format(len(telemetry_links), player_id))
    return telemetry_links


def get_telemetry_data(url):
    #telemetry_entry = get_cached_telemetry(url)
    telemetry_entry = None
    if not telemetry_entry:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                telemetry_entry = json.loads(resp.content.decode('utf-8'))
                cache_telemetry(url, telemetry_entry)
        except:
            print('something bad happened')
            telemetry_entry = []

    return telemetry_entry


if __name__ == "__main__":
    player_ids = {'1041', '779479758588243968', '776787878587011072', '132', '803650591871082496', '933', '3275', '786984970710310912', '821991447724175360', '885802503927644160', '1832', '781174824604164096', '289', '917233253176455168', '2106', '776043473915744256', '949654411112792064', '872272421724504064', '776122211131068416', '783003075697864704', '835837657555812352', '779862011638087680', '778293979656622080', '936282883222585344', '779117673312313344', '7854', '783445891691466752', '538', '778261434919424000', '777348984623730688', '825738634681528320', '778595379959717888', '131', '779528393816432640', '3511', '776666749549547520', '776450744541908992', '50', '804919733530013696', '777364499022876672', '3891', '948755982438277120', '2012', '927923317564911616', '776384000058068992', '776040988803207168', '783149438397984768', '777039017609924608', '778348927501082624', '781074452443181056'}
    all_telemetries = set()
    #clean_cache(created_ad)

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
