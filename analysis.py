from helpers import load_pickle, chunks, get_content
from furrycorn.location import mk_origin, mk_path, mk_query, to_url
import json
from ratelimiter import RateLimiter
import operator
from collections import defaultdict

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

with open('assets/gameplay.json', 'rb') as gplay:
    gplay = gplay.read()

def load_locale(path):
    with open(path, 'r') as f:
        data = [x.strip().split('=') for x in f]
        return {x[0]: x[1] for x in data}


locale_lookup = load_locale('assets/locale.loc')
characters = json.loads(gplay)['characters']
char_id_lookup = {x['typeID']: i for i,x in enumerate(characters)}


player_data = load_pickle('player_builds.p')
character_builds = load_pickle('character_builds.p')
#player_lookup = make_player_lookup([str(x) for x in player_data.keys()])

def sorted_by_count(x):
    return reversed(sorted(x.items(), key=operator.itemgetter(1)))

def make_brite_names(character_data, brite_lookup, brites):
    brite_names = []
    for b in brites:
        try:
            name = locale_lookup[character_data['battlerites'][brite_lookup[b]]['name']]
        except:
            name = "VERY UNKNOWN"
        brite_names.append(name)
    return brite_names

def render_character_builds(brite_lookup, character_data, character_dict, max_count=3):
    print('Most popular builds for {}:\n'.format(locale_lookup[character_data['name']]))
    num_builds = 0
    for build, count in sorted_by_count(character_dict):
        if num_builds >= max_count:
            break
        print(make_brite_names(character_data, brite_lookup, build), count)
        num_builds += 1


for mode, mode_dict in character_builds.items():
    print('Most popular builds in {}:\n'.format(mode))
    #Find most popular builds for each hero
    for hero_id, build_dict in mode_dict.items():
        character_data = characters[char_id_lookup[hero_id]]
        name = locale_lookup[character_data['name']]
        brite_lookup = {x['typeID']: i for i, x in enumerate(character_data['battlerites'])}
        render_character_builds(brite_lookup, character_data, build_dict)

    print('Most popular heroes in {}:\n'.format(mode))
    #Find most popular heroes
    appearance_summary = defaultdict(lambda: 0)
    for hero_id, build_dict in mode_dict.items():
        name = locale_lookup[characters[char_id_lookup[hero_id]]['name']]
        for build, count in build_dict.items():
            appearance_summary[name] += count

    print([x for x in sorted_by_count(appearance_summary)])