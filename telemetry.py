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
        user['battlerites'].append(brite)
    else:
        user['battlerites'] = [brite]


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

def print_brites(userItems):
    c = characters[char_id_lookup[userItems['character']]]
    print("\n")
    print(locale_lookup[c['name']])
    brite_lookup = {x['typeID']: i for i, x in enumerate(c['battlerites'])}
    for b in userItems['battlerites']:
        brite = c['battlerites'][brite_lookup[b]]
        print(locale_lookup[brite['name']])

for n, it in user_dict.items():
    print_brites(it)
