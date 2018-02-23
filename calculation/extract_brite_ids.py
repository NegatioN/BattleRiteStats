import re

rgx = re.compile('battlerite-stats.com/profile/(\d+)')

my_id = '957306926604132352'
with open('assets/brite.html', 'r', encoding="utf8") as f:
    text = f.read()

top_ids = set(rgx.findall(text))
if my_id in top_ids:
    top_ids.remove(my_id)
print(top_ids)