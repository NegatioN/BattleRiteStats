from helpers import load_pickle, chunks, get_content
from furrycorn.location import mk_origin, mk_path, mk_query, to_url
import json
from ratelimiter import RateLimiter

origin = mk_origin('https', 'api.dc01.gamelockerapp.com', '/shards/global')
headers = {'Accept': 'application/vnd.api+json',
           'Authorization': 'Bearer {0}'.format(api_key)}
rate_limiter = RateLimiter(max_calls=49, period=60)


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
player_lookup = make_player_lookup([str(x) for x in player_data.keys()])


for hero_id, builds in hero_builds.items():
    c = characters[char_id_lookup[hero_id]]
    brite_lookup = {x['typeID']: i for i, x in enumerate(c['battlerites'])}
    name = locale_lookup[c['name']]
    print('Most popular builds for {}:\n'.format(name))
    cc = 0
    for x, count in builds:
        if cc >= 3:
            break
        brite_names = make_brite_names(c, brite_lookup, x)
        print("\t{} : {}".format(brite_names, count))
        cc += 1




# print(get_player_names(c_data.keys()))
