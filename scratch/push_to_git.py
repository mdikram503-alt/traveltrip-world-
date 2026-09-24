import os
import subprocess
import glob

# Find git.exe
git_candidates = (
    glob.glob(r'C:\Users\HP\AppData\Local\GitHubDesktop\app-*\resources\app\git\cmd\git.exe') +
    [r'C:\Program Files\Git\cmd\git.exe', r'C:\Program Files\Git\bin\git.exe']
)

git_exe = None
for candidate in git_candidates:
    if os.path.exists(candidate):
        git_exe = candidate
        break

if not git_exe:
    # Try searching path
    import shutil
    git_exe = shutil.which('git')

print(f"Using git executable: {git_exe}")

if git_exe:
    # Run git status
    r1 = subprocess.run([git_exe, 'status', '--short'], capture_output=True, text=True)
    print("Status:\n", r1.stdout)
    
    # Add files
    subprocess.run([git_exe, 'add', 'supplier_service.py', 'server.py', 'public/index.html'], check=True)
    
    # Commit
    r2 = subprocess.run([git_exe, 'commit', '-m', 'Fix ResellPortal live API integration & instant buy provisioning'], capture_output=True, text=True)
    print("Commit:\n", r2.stdout, r2.stderr)
    
    # Push
    print("Pushing to origin main...")
    r3 = subprocess.run([git_exe, 'push', 'origin', 'main'], capture_output=True, text=True)
    print("Push Output:\n", r3.stdout, r3.stderr)
else:
    print("Error: git.exe could not be found.")
