import logging
import pathlib
import os
import subprocess
import re
import time
from datetime import datetime

######################### CONFIG ##############################
INTERVAL = 60
REPOS = {
    'pwnrex-paper': "/home/honululu/lukas/research/pwnrex/paper/pwnrex-paper",
    'pwnrex-paper-Lukas': "/home/honululu/lukas/research/pwnrex/paper/pwnrex-paper-Lukas-",
    'automatic_pwny': "/home/honululu/lukas/research/pwnrex/automatic_pwny",
    'automatic_pwny_samples': "/home/honululu/lukas/research/pwnrex/automatic_pwny_samples",
}


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRACK_DIR = pathlib.Path('~/.tracking').expanduser()
if not TRACK_DIR.exists():
    TRACK_DIR.mkdir()
REPOS = {name: (pathlib.Path(repo_dir), pathlib.Path(TRACK_DIR/name)) for name, repo_dir in REPOS.items()}



########################### UTIL ##############################
cwd = pathlib.Path(os.getcwd()).absolute().resolve()
assert (cwd / "rewind7am.py").is_file(), "All logging scripts have to be run in the main directory"

def rewind(t):
  return int(subprocess.check_output([str(cwd / "rewind7am.py"), str(t)]))


def get_timestamp():
    now = datetime.now().astimezone()
    s = now.isoformat()
    return s

def git(name, subcommand, *opts):
    repo_dir, track_dir = REPOS[name]
    env = {
        'GIT_DIR': track_dir,
        'GIT_WORK_TREE': repo_dir,
        'GIT_COMMITTER_NAME': 'ActivityTracker',
        'GIT_COMMITTER_EMAIL': '<>',
        'GIT_AUTHOR_NAME': 'ActivityTracker',
        'GIT_AUTHOR_EMAIL': '<>',
    }
    full_cmd = ['git', subcommand, *opts]
    log.info(f"git command: {repr(full_cmd)} @ {env!r}")
    return subprocess.check_output(full_cmd, cwd=repo_dir, env=env)


for name, (repo_dir, track_dir) in REPOS.items():
    if not track_dir.exists():
        track_dir.mkdir()
        log.info(f'Initializing repo tracking @ {track_dir} for {repo_dir}')
        git(name, 'init')
        git(name, 'config', 'user.name', 'ulogm_repo_logging')
        git(name, 'config', 'user.email', '<>')

cur_start = int(time.time())
while True:
    t = time.time()
    if t < cur_start + INTERVAL:
        wait = cur_start + INTERVAL - t
        log.info(f'Sleeping for {wait} seconds!')
        time.sleep(wait)
        continue

    log_file = f'logs/repo_changes_{rewind(cur_start)}.txt'
    cur_start += INTERVAL
    
    # git add -A
    # git commit -am "$message"
    for name in REPOS:
        log.info(f"updating repo {name}")
        message = f'Tracking update: {get_timestamp()}'

        inserted, file_changed, deleted = 0, 0, 0
        if git(name, 'status', '--porcelain').strip():
            git(name, 'add', '-A')
            output = git(name, 'commit', '-am', message)
            
            for match in re.finditer(' ([0-9]+) (deletion|insertion|file[s]? changed)', output.decode()):
                num, key = match.groups()
                num = int(num)
                if key in {'file changed', 'files changed'}:
                    file_changed = num
                elif key == 'insertion': 
                    inserted = num
                else:
                    deleted = num

        with open(log_file, 'a') as logf:
            logf.write(f'{cur_start} {name} {file_changed} {inserted} {deleted}\n')