#!/usr/bin/env python3
# -*- coding: utf-8
import requests
from urllib.parse import quote
import json
from ratelimiter import RateLimiter
from datetime import date, timedelta
import os

from helpers import chunks, get_content, pickle_info, get_telemtry
from collections import defaultdict
from furrycorn.location import mk_origin, mk_path, mk_query, to_url

api_key = os.environ.get('BATTLERITE_API_KEY')
print('Api key is set={}'.format("Yes" if api_key else "No"))
origin = mk_origin('https', 'api.dc01.gamelockerapp.com', '/shards/global')
headers = {'Accept': 'application/vnd.api+json',
           'Authorization': 'Bearer {0}'.format(api_key)}
rate_limiter = RateLimiter(max_calls=10, period=61)

#Last seven days of replays
created_after_date = '{}T08:00:00Z'.format((date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))

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

def get_player_ids(player_names):
    p_data = []
    for c in chunks(player_names, 5):
        p_data.append(get_player(c))
    return [y['id'] for x in p_data for y in x]

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


def find_match_type(telemetry_entry):
    for cursor in telemetry_entry:
        try:
            return cursor['dataObject']['serverType']
        except:
            pass
    return ""

def parse_battlerites(telemetry_entry):
    match_characters = defaultdict(lambda: defaultdict(lambda: set()))
    match_mode = find_match_type(telemetry_entry)
    for cursor in telemetry_entry:
        try:
            brite = cursor['dataObject']['battleriteType']
            userid = cursor['dataObject']['userID']
            character = cursor['dataObject']['character']
            match_characters[character][userid].add(brite)
        except:
            pass
    for character, d in match_characters.items():
        for userid, build in d.items():
            increment_build(frozenset(build), character, userid, match_mode)

def increment_build(brite_fset, character, player_id, match_mode):
    character_builds[match_mode][character][brite_fset] += 1
    player_builds[player_id][character][brite_fset] += 1


def get_telemetry_data(url):
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return json.loads(resp.content.decode('utf-8'))
    except:
        print('something bad happened')
        return []


if __name__ == "__main__":
    player_ids = {'1041', '779479758588243968', '776787878587011072', '132', '803650591871082496', '933', '3275', '786984970710310912', '821991447724175360', '885802503927644160', '1832', '781174824604164096', '289', '917233253176455168', '2106', '776043473915744256', '949654411112792064', '872272421724504064', '776122211131068416', '783003075697864704', '835837657555812352', '779862011638087680', '778293979656622080', '936282883222585344', '779117673312313344', '7854', '783445891691466752', '538', '778261434919424000', '777348984623730688', '825738634681528320', '778595379959717888', '131', '779528393816432640', '3511', '776666749549547520', '776450744541908992', '50', '804919733530013696', '777364499022876672', '3891', '948755982438277120', '2012', '927923317564911616', '776384000058068992', '776040988803207168', '783149438397984768', '777039017609924608', '778348927501082624', '781074452443181056'}
    all_telemetries = set()

    # For some reason this function returns duplicates ¯\_(ツ)_/¯
    #for player_id in get_player_ids(player_names):
    for player_id in player_ids:
        telems = get_player_telemetry(player_id)
        all_telemetries = all_telemetries.union(telems)

    character_builds = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))
    player_builds = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))

    print('{} match-telemetries'.format(len(all_telemetries)))

    for telem_url in all_telemetries:
        print('processing {}'.format(telem_url))
        parse_battlerites(get_telemetry_data(telem_url))


    pickle_info(character_builds, 'character_builds.p')
    pickle_info(player_builds, 'player_builds.p')
