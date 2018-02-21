from requests import Request, Session
import requests
from urllib.parse import quote
import json

from furrycorn import config, model, toolkit
from furrycorn.location import mk_origin, mk_path, mk_query, to_url
from furrycorn.toolkit.document import Data

player_names     = "NegatioNZor"

origin  = mk_origin('https', 'api.dc01.gamelockerapp.com', '/shards/global')
headers = { 'Accept': 'application/vnd.api+json',
            'Authorization': 'Bearer {0}'.format(api_key)}


def get_content(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.content)['data']
    else:
        return []

def get_document(url):
    request = Request('GET', url, headers=headers).prepare()
    response = Session().send(request)
    root     = model.build(response.json(), config.mk(origin, api_key))
    return toolkit.process(root)

def get_player_data(player_id):
    player_names = list(map(lambda n: quote(n), [player_id]))
    url = to_url(origin, mk_path('/players'), mk_query({ 'filter[playerNames]': player_names }))

    document = get_document(url)
    if type(document) is Data:
        p_data = []
        for player in document:
            p_data.append(player.maybe_dict_attrs)
        return p_data
    else:
        return None

def get_match_info(player_id, offset=0):
    player_ids = list(map(lambda n: quote(n), [player_id]))
    url = to_url(origin, mk_path('/matches'), mk_query({ 'filter[playerIds]': player_ids, 'page[offset]': offset}))
    document = get_document(url)
    telemetry_links = []
    if type(document) is Data:
        for match in document:
            for asset in match.traverse('assets'):
                if asset.maybe_dict_attrs.get('name', None):
                    url = asset.maybe_dict_attrs['URL']
                    telemetry_links.append(url)
    return telemetry_links


def get_player_match(player_id):
    player_ids = list(map(lambda n: quote(n), [player_id]))
    url = to_url(origin, mk_path('/matches'), mk_query({ 'filter[playerIds]': player_ids }))
    return get_content(url)

def get_player(player_name):
    player_names = list(map(lambda n: quote(n), [player_name]))
    url = to_url(origin, mk_path('/players'), mk_query({ 'filter[playerNames]': player_names }))
    return get_content(url)


#pprint(get_player_data(player_names))
#get_match_info(2)
#print(get_player("Averse"))
#get_player_match("957306926604132352")
count = 10
max_count = count + 10
step = 5
telemetry_links = []
while count < max_count:
    print(count)
    t_links = get_match_info("776450744541908992", offset=step*count)
    telemetry_links.append(t_links)
    count += 1

telemetry_links = [y for x in telemetry_links for y in x]

import os

def get_player_telemetry(telemetry_links):
    telemetry = []
    for url in telemetry_links:
        print('getting {}'.format(url))
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                telemetry.append(json.loads(resp.content))
        except:
            print('something bad happened')
    fname = '{}_telemetry.json'.format('averse')
    if os.path.isfile(fname):
        with open(fname, "r") as f:
            content = json.load(f)

        telemetry.extend(content)
        print("Extended content")

    with open(fname, 'w+') as f:
        json.dump(telemetry, f)

get_player_telemetry(telemetry_links)

