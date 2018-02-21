import json
from pprint import pprint

with open('test_telemetry.json', 'rb') as telemetry_json:
    raw       = telemetry_json.read()
with open('gameplay.json', 'rb') as gplay:
    gplay       = gplay.read()

def load_locale(path):
    with open(path, 'r') as f:
        data = [x.strip().split('=') for x in f]
        return {x[0]: x[1] for x in data}


locale_lookup = load_locale('locale.loc')
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

def print_brites(char_id, brites):
    c = characters[char_id_lookup[char_id]]
    brite_lookup = {x['typeID']: i for i, x in enumerate(c['battlerites'])}
    name = locale_lookup[c['name']]
    brite_names = []
    for b in brites:
        brite = c['battlerites'][brite_lookup[b]]
        brite_names.append(locale_lookup[brite['name']])

    print("{}: {}".format(name, brite_names))

from collections import defaultdict

brites_count = defaultdict(lambda: [0, ""])

for k,x in user_dict.items():
    brites_count[frozenset(x['battlerites'])][1] = x['character']
    brites_count[frozenset(x['battlerites'])][0] += 1

import operator
def sorted_by_count(x):
    return sorted(x.items(), key=operator.itemgetter(1))
for x in sorted_by_count(brites_count):
    print_brites(char_id=x[1][1], brites=x[0])
    print(x[1][0])
