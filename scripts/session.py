"""
session.py
Session lifecycle.

  open   : git pull --rebase + Odoo pull to exports/latest.json + log OPEN
  close  : Odoo pull + log CLOSE + git commit + push
  pull   : just the Odoo pull (no git), useful ad-hoc

Filter approach for Odoo To-do isolation:
  - project_id = False    (To-do tasks have NO project; project tasks excluded)
  - personal_stage_type_ids IN <5 open stage ids>  (Inbox, Today, This Week,
                           Next Week, Later — Done and Cancelled excluded)
  - active = True
  - state not in done/cancelled
  - user_ids in [uid]     (safety)
"""
import json
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPTS_DIR.parent
EXPORTS_DIR = REPO_DIR / 'exports'
SESSIONS_LOG = EXPORTS_DIR / 'sessions.log'
LATEST_EXPORT = EXPORTS_DIR / 'latest.json'
CONFIG_PATH = SCRIPTS_DIR / 'config.json'

STAGE_NAMES = ['Inbox', 'Today', 'This Week', 'Next Week', 'Later']


def machine():
    return socket.gethostname().replace('.local', '').replace('.lan', '')


def now_iso():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def git(*args):
    return subprocess.run(
        ['git', '-C', str(REPO_DIR)] + list(args),
        capture_output=True, text=True
    )


def log_event(event, extra=''):
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{now_iso()} | {event:<5} | {machine():<20} | {extra}\n"
    with open(SESSIONS_LOG, 'a') as f:
        f.write(line)


def last_event(event_type):
    if not SESSIONS_LOG.exists():
        return None
    with open(SESSIONS_LOG) as f:
        for line in reversed(f.readlines()):
            if f"| {event_type:<5} |" in line:
                return line.strip()
    return None


def fetch_personal_stages(c):
    """Return dict name -> id for the 5 named open personal stages."""
    stages = c.search_read(
        'project.task.type',
        domain=[('user_id', '=', c._uid), ('name', 'in', STAGE_NAMES)],
        fields=['id', 'name', 'sequence'],
        order='sequence',
    )
    return {s['name']: s['id'] for s in stages}


def todo_domain_for_stages(uid, stage_ids, include_done=False):
    """Domain for Odoo To-do tasks in the 5 open stages only.
    CRITICAL: project_id=False isolates To-do from regular project tasks."""
    d = [
        ('project_id', '=', False),
        ('user_ids', 'in', [uid]),
        ('personal_stage_type_ids', 'in', stage_ids),
        ('active', '=', True),
    ]
    if not include_done:
        d.append(('state', 'not in', ['1_done', '1_canceled']))
    return d


def pull_odoo_tasks():
    """Pull OPEN personal To-do tasks, write exports/latest.json.
    Returns (count, error_or_None)."""
    if not CONFIG_PATH.exists():
        return (0, "config.json missing — run: session setup")
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from odoo_client import OdooClient
        c = OdooClient(CONFIG_PATH)
        c.connect()

        stage_map = fetch_personal_stages(c)
        missing = [n for n in STAGE_NAMES if n not in stage_map]
        if missing:
            return (0,
                f"Missing personal stages: {missing}. "
                f"Found: {list(stage_map.keys())}. "
                f"Create them in Odoo To-do and retry.")
        stage_ids = list(stage_map.values())

        tasks = c.search_read(
            'project.task',
            domain=todo_domain_for_stages(c._uid, stage_ids),
            fields=[
                'id', 'name', 'description',
                'project_id', 'stage_id',
                'personal_stage_type_ids', 'personal_stage_type_id',
                'tag_ids', 'priority', 'state', 'active',
                'date_deadline', 'date_end',
                'user_ids', 'sequence',
                'write_date', 'create_date',
            ],
            order='sequence, id'
        )

        personal_stages = c.search_read(
            'project.task.type',
            domain=[('user_id', '=', c._uid)],
            fields=['id', 'name', 'sequence', 'user_id'],
            order='sequence'
        )
        tags = c.search_read(
            'project.tags',
            domain=[],
            fields=['id', 'name', 'color'],
            order='name'
        )

        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        snapshot = {
            'pulled_at': now_iso(),
            'machine': machine(),
            'uid': c._uid,
            'stage_map': stage_map,
            'task_count': len(tasks),
            'tasks': tasks,
            'personal_stages': personal_stages,
            'tags': tags,
        }
        with open(LATEST_EXPORT, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)
        return (len(tasks), None)
    except Exception as e:
        return (0, str(e))


def open_session():
    print(f"Opening session on {machine()} at {now_iso()}\n")

    print("[1/3] git pull --rebase origin main")
    r = git('pull', '--rebase', 'origin', 'main')
    if r.returncode == 0:
        tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'OK'
        print(f"       {tail}")
    else:
        print(f"       WARN: {r.stderr.strip()}")

    print("\n[2/3] Last CLOSE event:")
    last_close = last_event('CLOSE')
    print(f"       {last_close}" if last_close else "       (none recorded yet)")

    print("\n[3/3] Pulling Odoo To-do tasks...")
    count, err = pull_odoo_tasks()
    if err:
        print(f"       SKIPPED: {err}")
        log_event('OPEN', 'odoo_pull=skipped')
    else:
        print(f"       {count} open To-do tasks -> exports/latest.json")
        log_event('OPEN', f'odoo_tasks={count}')

    print(f"\nSession open on {machine()}. Ready to work.")


def close_session():
    print(f"Closing session on {machine()} at {now_iso()}\n")

    print("[1/3] Pulling final Odoo To-do tasks...")
    count, err = pull_odoo_tasks()
    if err:
        print(f"       SKIPPED: {err}")
        extra = 'odoo_pull=skipped'
    else:
        print(f"       {count} open To-do tasks pulled")
        extra = f'odoo_tasks={count}'
    log_event('CLOSE', extra)

    print("\n[2/3] Committing changes...")
    r = git('status', '--porcelain')
    if not r.stdout.strip():
        print("       Nothing to commit.")
    else:
        git('add', '-A')
        msg = f"session close from {machine()} {now_iso()}"
        r = git('commit', '-m', msg)
        if r.returncode == 0:
            print(f"       {msg}")
        else:
            print(f"       Commit issue: {r.stderr.strip()}")

    print("\n[3/3] git push origin main")
    r = git('push', 'origin', 'main')
    if r.returncode == 0:
        print("       Pushed")
    else:
        print(f"       WARN: {r.stderr.strip()}")

    print(f"\nSession closed on {machine()}. Safe to switch machines.")


def pull_only():
    count, err = pull_odoo_tasks()
    if err:
        print(f"ERROR: {err}")
        sys.exit(1)
    print(f"{count} open To-do tasks pulled to exports/latest.json")


def main():
    if len(sys.argv) < 2:
        print("Usage: session.py open|close|pull")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'open':
        open_session()
    elif cmd == 'close':
        close_session()
    elif cmd == 'pull':
        pull_only()
    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
