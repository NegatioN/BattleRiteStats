import ntpath
from datetime import datetime
import os
import json
import shutil

telemetry_base_path = 'https://cdn.gamelockerapp.com/stunlock-studios-battlerite/global/'
cache_dir = 'cache'

def extract_telem_path(telem_url): return telem_url.replace(telemetry_base_path, '')
def to_cache_dir(p): return os.path.join(cache_dir, p)

def mkdir_path(path):
    if not os.access(path, os.F_OK):
        os.makedirs(path)

def get_n_folder_levels(path, n):
    d = {}
    for root, dirs, files in os.walk(path):
        if root.count(os.sep) < n:
            ps = root.split('/')
            cur_d = d
            for p in ps:
                if p not in cur_d:
                    cur_d[p] = {}
                cur_d = cur_d[p]
    return d

class TelemetryCache:
    def __init__(self):
        self.cache_hits = 0
        self.added_to_cache = 0

    def get_cached_telemetry(self, telemetry_url):
        telem_path = to_cache_dir(extract_telem_path(telemetry_url))
        if os.path.exists(telem_path):
            with open(telem_path, 'r', encoding='utf-8') as f:
                self.cache_hits += 1
                return json.load(f)
        else:
            return None

    def cache_telemetry(self, telemetry_url, content):
        telem_path = to_cache_dir(extract_telem_path(telemetry_url))
        head, tail = ntpath.split(telem_path)
        mkdir_path(head)
        with open(telem_path, 'w+', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False)
            self.added_to_cache += 1

    '''Clears out cached files from before the limit-datetime passed.'''
    def clean_cache(self, limit_datetime):
        paths = get_n_folder_levels(cache_dir, 4)[cache_dir]
        dates = set()
        for year, d in paths.items():
            for month, y in d.items():
                for day, _ in y.items():
                    dates.add(datetime(year=int(year), month=int(month), day=int(day)))

        deletable_dates = [x for x in dates if x < limit_datetime]
        for d in deletable_dates:
            date_path = os.path.join(cache_dir, d.strftime('%Y/%m/%d'))
            shutil.rmtree(date_path)

        print('Cleaned cached telemetry older than: {}'.format(limit_datetime.strftime('%Y-%m-%d')))
