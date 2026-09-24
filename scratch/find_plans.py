import re

content = open('public/index.html', encoding='utf-8').read()
matches = re.findall(r'id:"[^"]+",title:"[^"]+",flag:"[^"]+",data:"[^"]+"[^\}]+', content)
for m in matches[:5]:
    print(m)
