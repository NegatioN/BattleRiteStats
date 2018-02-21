from requests import Request, Session
from urllib.parse import quote
from pprint import pprint
import pdb
import json

from furrycorn import config, model, toolkit
from furrycorn.location import mk_origin, mk_path, mk_query, to_url
from furrycorn.toolkit.document import Data


# Set the BATTLERITE_PLAYER_NAME environment variable to a list of
# comma-separated names to get information from the API.
player_names     = "NegatioNZor"

origin  = mk_origin('https', 'api.dc01.gamelockerapp.com', '/shards/global')
headers = { 'Accept': 'application/vnd.api+json',
            'Authorization': 'Bearer {0}'.format(api_key)}


def get_content(url):
    request = Request('GET', url, headers=headers).prepare()
    session = Session()
    response = session.send(request)
    if response.status_code == 200:
        return json.loads(response.content)['data']
    else:
        return []

def get_document(url):
    request = Request('GET', url, headers=headers).prepare()
    session = Session()
    response = session.send(request)
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

def get_match_info(player_id):
    player_ids = list(map(lambda n: quote(n), [player_id]))
    url = to_url(origin, mk_path('/matches'), mk_query({ 'filter[playerIds]': player_ids }))
    document = get_document(url)
    if type(document) is Data:
        for match in document:
            print('match id "{0}"'.format(match.resource_id.r_id))

            # We know before the 'assets' has one entry--the telmetry. But...
            # madglory exposes this as 'to many', so we dig.
            for asset in match.traverse('assets'):
                if asset.maybe_dict_attrs.get('name', None):
                    url = asset.maybe_dict_attrs['URL']
                    print('  telemetry at: {0}'.format(url))

            # Let's see how many rounds happened this match:
            round_ct = len(match.traverse('rounds'))
            print('  round count: {0}'.format(round_ct))

            # And let's peek at the first roster's attributes:
            first_roster = match.traverse('rosters')[0]
            print('  roster #1 attrs: {0}'.format(first_roster.maybe_dict_attrs))

def get_player_match(player_id):
    player_ids = list(map(lambda n: quote(n), [player_id]))
    url = to_url(origin, mk_path('/matches'), mk_query({ 'filter[playerIds]': player_ids }))
    content = get_content(url)
    pdb.set_trace()

def get_player(player_name):
    player_names = list(map(lambda n: quote(n), [player_name]))
    url = to_url(origin, mk_path('/players'), mk_query({ 'filter[playerNames]': player_names }))
    return get_content(url)


#pprint(get_player_data(player_names))
#get_match_info(2)
#get_player("NegatioNZor")
get_player_match("957306926604132352")

