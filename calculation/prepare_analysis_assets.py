from git import Repo
import os
import shutil
from helpers import path_leaf


to_dir = 'assets'
num_asset_editions = 2

repo_dir = 'assets/brite_assets'
if not os.path.isdir(repo_dir):
    Repo.clone_from('https://github.com/gamelocker/battlerite-assets.git', repo_dir)
repo = Repo(repo_dir)
o = repo.remotes.origin
o.pull()

mappings_dir = '{}/mappings'.format(repo_dir)
int_dirs = []
for x in  os.listdir(mappings_dir):
    try:
        int_dirs.append(int(x))
    except:
        pass
newest_dirs = [os.path.join(mappings_dir, str(x)) for x in list(reversed(sorted(int_dirs)))[:num_asset_editions]]
print('Getting assets from {}'.format(newest_dirs))

filenames = ['gameplay.json', 'Localization/English.ini']

for i, y in enumerate(newest_dirs):
    for x in filenames:
        shutil.copy(os.path.join(y, x), os.path.join(to_dir, '{}_{}'.format(i, path_leaf(x))))
