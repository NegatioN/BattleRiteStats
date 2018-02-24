from git import Repo
import os
import shutil
import ntpath

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

to_dir = 'assets'

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

newest_dir = os.path.join(mappings_dir, str([x for x in reversed(sorted(int_dirs))][0]))

print('Getting assets from {}'.format(newest_dir))

filenames = ['gameplay.json', 'Localization/English.ini']

for x in filenames:
    shutil.copy(os.path.join(newest_dir, x), os.path.join(to_dir, path_leaf(x)))

