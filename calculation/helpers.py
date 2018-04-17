#!/usr/bin/env python3
# -*- coding: utf-8
import requests
import json
import pickle
import ntpath
import re
from bs4 import BeautifulSoup
from collections import defaultdict
import numpy as np
from ratelimiter import RateLimiter

def get_content(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
        return []

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

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

'''Kinda manual method for getting color-scheme of character skills for now. Just run for all heros'''
def bootstrap_character_colors(hero_name):
    cont = requests.get('https://battlerite.gamepedia.com/{}/Battlerites'.format(hero_name.replace(' ', '_'))).text
    bs = BeautifulSoup(cont, "html.parser")
    stuff = bs.find_all('div', {'class': 'battlerite'})
    char_colors = []
    for s in stuff:
        title = s.find('div', {'class': 'battlerite--title'}).p.text
        color_alt = s.find('div', {'class': 'battlerite--art'}).img['alt']
        color = re.split('\s', color_alt)[-1].split('.')[0].lower()
        char_colors.append({'title': title, 'color': color})
    return char_colors

battlerite_type_mapping = {1: {'color': 'red', 'type': 'offense'},
                           2: {'color': 'yellow', 'type': 'mobility'},
                           3: {'color': 'blue', 'type': 'utility'},
                           4: {'color': 'green', 'type': 'survival'},
                           5: {'color': 'pink', 'type': 'control'},
                           6: {'color': 'teal', 'type': 'support'},
                           7: {'color': 'grey', 'type': 'mixed'}}

def get_battlerite_color_mapping():
    with open('battlerites_type_mappings.json', 'r') as f:
        defined_mappings = json.load(f)
        color_mappings = defaultdict(lambda: battlerite_type_mapping[7]['color'])
        for k, v in defined_mappings.items():
            color_mappings[k] = battlerite_type_mapping[v]['color']
        return color_mappings


def get_battlerite_type_mapping():
    with open('battlerites_type_mappings.json', 'r') as f:
        defined_mappings = json.load(f)
        type_mappings = defaultdict(lambda: battlerite_type_mapping[7]['type'])
        for k, v in defined_mappings.items():
            type_mappings[k] = battlerite_type_mapping[v]['type']
        return type_mappings


def get_proxies():
    try:
        rate_limiter = RateLimiter(max_calls=30, period=60)
        proxy = {'supportsHttps': False, 'speed': 0, 'protocol': 'yolo', 'post': False}
        while not (proxy['speed'] > 30
                   and proxy['supportsHttps']
                   and proxy['post']
                   and proxy['protocol'] == 'http'):
            with rate_limiter:
                proxy = requests.get('https://gimmeproxy.com/api/getProxy').json()
        proxies = {'http': 'http://{}'.format(proxy['ipPort']), 'https': 'https://{}'.format(proxy['ipPort'])}
    except:
        proxies = None
    return proxies

def get_user_ids():
    proxies = get_proxies()
    print('Using proxy: {}'.format(proxies))
    query_url = 'https://battlerite-stats.com/leaderboards'
    ids = []
    offset = 0
    session = requests.Session()
    resp = session.get(query_url, proxies=proxies)
    session_cookies = session.cookies.get_dict()
    bs = BeautifulSoup(resp.content, "html.parser")
    csrf_token = bs.find('meta', {'name': 'csrf-token'})['content']
    cookies = 'theme={theme}; lang={lang}; XSRF-TOKEN={XSRF-TOKEN}; laravel_session={laravel_session}'.format(**session_cookies)
    headers = {'X-CSRF-TOKEN': csrf_token,
               'Cookie': cookies}

    only_grand_champions = True
    rate_limiter = RateLimiter(max_calls=10, period=60)
    while only_grand_champions:
        with rate_limiter:
            response = requests.post(query_url, headers=headers, data={'id': offset}, proxies=proxies)
            bs = BeautifulSoup(response.json()['blocks'], "html.parser")
            cur_ids = [x['href'].replace('https://battlerite-stats.com/profile/', '')
                       for x in bs.find_all('a', {'class': 'table-row-link'})]
            divisions = bs.find_all('div', {'class': 'league-name'})

            only_grand_champions = np.all([True if x.text in ['Grand Champion', 'Champion League'] else False
                                           for x in divisions])
            offset += 50
            ids.extend(cur_ids)
            if offset >= 500:
                # Battlerite-stats seems to only display this many on their leaderboard.
                break

    return ids
