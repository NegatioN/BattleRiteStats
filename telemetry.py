import json
import operator
from collections import defaultdict

with open('averse_telemetry.json', 'rb') as telemetry_json:
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

#types = ['QUICK2V2', 'QUICK3v3']
types = ['RANKED']

for ob in json.loads(raw):
    found_server_type = False
    server_type = ""
    for cursor in ob:
        try:
            if found_server_type:
                break
            #print("{}: {}".format(cursor['dataObject']['mode'], cursor['dataObject']['teamSize']))
            #server_type = cursor['dataObject']['serverType']
            server_type = cursor['dataObject']['mode']
            found_server_type = True
        except:
            pass
    if server_type in types:
        for cursor in ob:
            try:
                brite = cursor['dataObject']['battleriteType']
                #User is currently matchid + userid, to keep a user unique without rewriting logic. lazyboiz
                userid = '{}-{}'.format(cursor['dataObject']['userID'], cursor['dataObject']['matchID'])

                if userid not in user_dict:
                    character = cursor['dataObject']['character']
                    user_dict[userid] = {'character': character}

                insert_battlerite(brite, user_dict[userid])
            except:
                pass

print(len(user_dict))
def make_brite_names(c, brite_lookup, brites):
    brite_names = []
    for b in brites:
        try:
            brite = c['battlerites'][brite_lookup[b]]
            name = locale_lookup[brite['name']]
        except:
            name = "VERY UNKNOWN"
        brite_names.append(name)
    return brite_names

brites_count = defaultdict(lambda: [0, ""])

for k,x in user_dict.items():
    fs_brites = frozenset(x['battlerites'])
    brites_count[fs_brites][1] = x['character']
    brites_count[fs_brites][0] += 1

def sorted_by_count(x):
    return reversed(sorted(x.items(), key=operator.itemgetter(1)))

hero_builds = defaultdict(lambda: [])
for k,v in sorted_by_count(brites_count):
    hero_builds[v[1]].append((k, v[0]))

print(len(hero_builds))

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

