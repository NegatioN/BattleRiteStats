import requests
import json
import pickle
from collections import defaultdict

def chunks(arr, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(arr), n):
        yield arr[i:i + n]


def get_content(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.content)['data']
    else:
        return []

def get_telemtry(url, headers):
    response = requests.get(url, headers=headers)
    match_ids = set()
    telemetry_urls = set()
    if response.status_code == 200:
        content = json.loads(response.content)
        all_data_nodes = content['data']
        for n in all_data_nodes:
            match_ids.add(n['relationships']['assets']['data'][0]['id'])

        for node in content['included']:
            if 'id' in node and node['id'] in match_ids:
                telemetry_urls.add(node['attributes']['URL'])

        return telemetry_urls
    else:
        return set()

def default_to_regular(d):
    if isinstance(d, defaultdict):
        d = {k: default_to_regular(v) for k, v in d.items()}
    return d

def pickle_info(build_info, filename):
    with open('assets/{}'.format(filename), 'wb+') as f:
        f.write(pickle.dumps(default_to_regular(build_info)))

def load_pickle(filename):
    with open('assets/{}'.format(filename), 'rb') as f:
        return pickle.loads(f.read())