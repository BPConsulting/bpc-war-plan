"""
setup.py
First-time setup for this machine:
  - Verifies/creates scripts/config.json (Odoo URL, DB, user — not secret)
  - Prompts for Odoo password, stores in macOS Keychain
  - Tests connection
"""
import json
import subprocess
import sys
from pathlib import Path
from getpass import getpass

SCRIPTS_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPTS_DIR / 'config.json'


def prompt(label, default=None, required=True):
    suffix = f" [{default}]" if default else ""
    while True:
        v = input(f"{label}{suffix}: ").strip()
        if not v and default is not None:
            return default
        if v or not required:
            return v
        print("  Required — try again.")


def keychain_set(service, account, password):
    r = subprocess.run(
        ['security', 'add-generic-password',
         '-a', account, '-s', service, '-w', password, '-U'],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"Keychain write failed: {r.stderr}")


def keychain_get(service, account):
    r = subprocess.run(
        ['security', 'find-generic-password',
         '-a', account, '-s', service, '-w'],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        return r.stdout.strip()
    return None


def test_connection():
    print("\nTesting connection...")
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from odoo_client import OdooClient
        c = OdooClient(CONFIG_PATH)
        uid = c.connect()
        print(f"OK — authenticated, uid={uid}")
        print("\nSetup complete. Try: session open")
        return True
    except Exception as e:
        print(f"FAILED — {e}")
        return False


def main():
    print("BPC War Room — setup on this machine")
    print("=" * 50)

    # Config
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        print(f"\nConfig found at {CONFIG_PATH}:")
        print(f"  url:  {cfg.get('url')}")
        print(f"  db:   {cfg.get('db')}")
        print(f"  user: {cfg.get('user')}")
        edit = input("\nEdit? [y/N] ").strip().lower()
        if edit == 'y':
            cfg = None
    else:
        print(f"\nNo config at {CONFIG_PATH} — creating one.")
        cfg = None

    if cfg is None:
        cfg = {
            'url': prompt("Odoo URL", default='https://bpconsulting.com.my'),
            'db': prompt("Database name"),
            'user': prompt("Username (login email)"),
            'keychain_service': 'bpc-war-room',
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(cfg, f, indent=2)
        print(f"Wrote {CONFIG_PATH}")

    # Keychain password
    existing = keychain_get(cfg['keychain_service'], cfg['user'])
    if existing:
        print(f"\nPassword already in Keychain for {cfg['user']}")
        overwrite = input("Replace? [y/N] ").strip().lower()
        if overwrite != 'y':
            print("Keeping existing password.")
            test_connection()
            return

    print(f"\nEnter Odoo password for {cfg['user']}")
    print("(stored in macOS Keychain, never written to any file)")
    pwd = getpass("Password: ")
    if not pwd:
        print("Aborted — empty password.")
        sys.exit(1)

    keychain_set(cfg['keychain_service'], cfg['user'], pwd)
    print(f"Stored in Keychain: service='{cfg['keychain_service']}' account='{cfg['user']}'")

    if not test_connection():
        sys.exit(1)


if __name__ == '__main__':
    main()
