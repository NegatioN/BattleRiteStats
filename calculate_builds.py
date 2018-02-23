import requests
from urllib.parse import quote
import json
from ratelimiter import RateLimiter

from furrycorn.location import mk_origin, mk_path, mk_query, to_url
from helpers import chunks, get_content, pickle_info, get_telemtry
from collections import defaultdict

origin = mk_origin('https', 'api.dc01.gamelockerapp.com', '/shards/global')
headers = {'Accept': 'application/vnd.api+json',
           'Authorization': 'Bearer {0}'.format(api_key)}
rate_limiter = RateLimiter(max_calls=9, period=60)
created_after_date = '2018-02-15T08:00:00Z'


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
            print(count)
            t_links = get_match_info(player_id, offset=step * count)
            if len(t_links) > 0:
                telemetry_links.append(t_links)
                count += 1
            else:
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
    character_builds[character][match_mode][brite_fset] += 1
    player_builds[player_id][character][brite_fset] += 1


def get_telemetry_data(url):
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return json.loads(resp.content)
    except:
        print('something bad happened')
        return []


if __name__ == "__main__":
    player_names = ['Averse', 'Techzz', 'YourN1ghtmare-', 'Aldys', 'Bocajs', 'Hotbiscuit', 'Tonho', 'ProsteR18', 'MrHuDat', 'youtube.com/c/cr7dabaixada']
    all_telemetries = set()

    # For some reason this function returns duplicates ¯\_(ツ)_/¯
    for player_id in get_player_ids(player_names):
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
