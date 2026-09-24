import urllib.request
import re

req = urllib.request.Request('https://traveltripworld.appserviceportal.com/', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as res:
    html = res.read().decode('utf-8', errors='ignore')

# Find buttons and modal triggers
matches = re.findall(r'<button[^>]+>', html)
for m in matches[:10]:
    print(m)
