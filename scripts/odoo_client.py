"""
odoo_client.py
Shared Odoo XML-RPC client for BPC War Room scripts.
Password is read from macOS Keychain (per machine).
"""
import json
import subprocess
import xmlrpc.client
from pathlib import Path


class OdooClient:
    def __init__(self, config_path):
        config_path = Path(config_path)
        if not config_path.exists():
            raise RuntimeError(
                f"Config not found: {config_path}\nRun: bpc setup"
            )
        with open(config_path) as f:
            cfg = json.load(f)
        self.url = cfg['url'].rstrip('/')
        self.db = cfg['db']
        self.user = cfg['user']
        self.keychain_service = cfg.get('keychain_service', 'bpc-war-room')
        self._uid = None
        self._password_cache = None
        self._models = None

    # ---------------- password ----------------

    def _password(self):
        if self._password_cache is not None:
            return self._password_cache
        r = subprocess.run(
            ['security', 'find-generic-password',
             '-a', self.user,
             '-s', self.keychain_service,
             '-w'],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            raise RuntimeError(
                f"Password not found in Keychain for account '{self.user}', "
                f"service '{self.keychain_service}'.\nRun: bpc setup"
            )
        self._password_cache = r.stdout.strip()
        return self._password_cache

    # ---------------- connection ----------------

    def connect(self):
        if self._uid is not None:
            return self._uid
        common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        try:
            uid = common.authenticate(self.db, self.user, self._password(), {})
        except Exception as e:
            raise RuntimeError(f"Cannot reach Odoo at {self.url}: {e}")
        if not uid:
            raise RuntimeError(
                f"Authentication failed for {self.user}@{self.db}.\n"
                f"Check username, or run: bpc setup"
            )
        self._uid = uid
        self._models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        return uid

    # ---------------- helpers ----------------

    def search_read(self, model, domain=None, fields=None, limit=0, order=''):
        self.connect()
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        if limit:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order
        return self._models.execute_kw(
            self.db, self._uid, self._password(),
            model, 'search_read', [domain or []], kwargs
        )

    def create(self, model, vals):
        self.connect()
        return self._models.execute_kw(
            self.db, self._uid, self._password(),
            model, 'create', [vals]
        )

    def write(self, model, ids, vals):
        self.connect()
        return self._models.execute_kw(
            self.db, self._uid, self._password(),
            model, 'write', [ids, vals]
        )

    def unlink(self, model, ids):
        self.connect()
        return self._models.execute_kw(
            self.db, self._uid, self._password(),
            model, 'unlink', [ids]
        )

    def execute(self, model, method, *args, **kwargs):
        self.connect()
        return self._models.execute_kw(
            self.db, self._uid, self._password(),
            model, method, list(args), kwargs
        )
