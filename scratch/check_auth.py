content = open('public/index.html', encoding='utf-8').read()

# Let's inspect where login / signup / forgot is handled
import re

# Find login function in public/index.html
# Earlier we saw:
# Ln==="login"?"Login":Ln==="signup"?"Create account":"Send reset link"
# o("button",{onClick:Bf, ...})
idx = content.find('Bf=')
if idx == -1:
    idx = content.find('Bf =')

print("Bf index:", idx)
if idx != -1:
    print(content[idx:idx+800].encode('ascii', 'replace').decode())
else:
    # search around 'Create account'
    c_idx = content.find('Create account')
    print("Create account around:\n", content[max(0, c_idx-500):min(len(content), c_idx+500)].encode('ascii', 'replace').decode())
