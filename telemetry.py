import json

with open('assets/test_telemetry.json', 'rb') as telemetry_json:
    raw       = telemetry_json.read()
with open('assets/gameplay.json', 'rb') as gplay:
    gplay       = gplay.read()

def load_locale(path):
    with open(path, 'r') as f:
        data = [x.strip().split('=') for x in f]
        return {x[0]: x[1] for x in data}


locale_lookup = load_locale('assets/locale.loc')
characters = json.loads(gplay)['characters']
char_id_lookup = {x['typeID']: i for i,x in enumerate(characters)}
user_dict = {}

def insert_battlerite(brite, user):
    if 'battlerites' in user:
        user['battlerites'].add(brite)
    else:
        user['battlerites'] = {brite}


for cursor in json.loads(raw):
    try:
        brite = cursor['dataObject']['battleriteType']
        userid = cursor['dataObject']['userID']

        if userid not in user_dict:
            character = cursor['dataObject']['character']
            user_dict[userid] = {'character': character}

        insert_battlerite(brite, user_dict[userid])
    except:
        pass

def make_brite_names(brite_lookup, brites):
    brite_names = []
    for b in brites:
        brite = c['battlerites'][brite_lookup[b]]
        brite_names.append(locale_lookup[brite['name']])
    return brite_names

from collections import defaultdict

brites_count = defaultdict(lambda: [0, ""])

for k,x in user_dict.items():
    brites_count[frozenset(x['battlerites'])][1] = x['character']
    brites_count[frozenset(x['battlerites'])][0] += 1

import operator
def sorted_by_count(x):
    return sorted(x.items(), key=operator.itemgetter(1))

hero_builds = defaultdict(lambda: [])
for k,v in sorted_by_count(brites_count):
    hero_builds[v[1]].append(k)

for hero_id, builds in hero_builds.items():
    c = characters[char_id_lookup[hero_id]]
    brite_lookup = {x['typeID']: i for i, x in enumerate(c['battlerites'])}
    name = locale_lookup[c['name']]
    for x in builds:
        brite_names = make_brite_names(brite_lookup, x)
        print("{}: {}".format(name, brite_names))

