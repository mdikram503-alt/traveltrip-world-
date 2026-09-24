import urllib.request
import re

req = urllib.request.Request('https://traveltripworld.appserviceportal.com/', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as res:
    html = res.read().decode('utf-8', errors='ignore')

idx = html.find('purchase-modal')
if idx != -1:
    print(html[idx:idx+1500])
else:
    print('purchase-modal not found')
