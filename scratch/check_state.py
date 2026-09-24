content = open('public/index.html', encoding='utf-8').read()

# Find App component state initialization
idx = content.find('Bf=')
print("Snippet before Bf:\n", content[idx-800:idx].encode('ascii', 'replace').decode())
