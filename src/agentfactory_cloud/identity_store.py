"""SQLite persistence for the single Cloud identity authority; no HTTP entrypoint."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import threading


class IdentityStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.lock = threading.RLock()
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS identity_accounts(
          id TEXT PRIMARY KEY, status TEXT NOT NULL, login_hash TEXT, recovery_hash TEXT,
          generation INTEGER NOT NULL, age_band TEXT NOT NULL, jurisdiction TEXT NOT NULL,
          provider_route TEXT NOT NULL, policy_ref TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS identity_memberships(
          account_id TEXT NOT NULL REFERENCES identity_accounts(id), tenant_id TEXT NOT NULL,
          role TEXT NOT NULL, PRIMARY KEY(account_id,tenant_id,role));
        CREATE TABLE IF NOT EXISTS identity_sessions(
          token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES identity_accounts(id),
          generation INTEGER NOT NULL, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS identity_rates(
          key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS identity_audit(
          id INTEGER PRIMARY KEY, account_id TEXT, action TEXT NOT NULL,
          outcome TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS identity_deletions(
          account_id TEXT PRIMARY KEY REFERENCES identity_accounts(id), status TEXT NOT NULL,
          requested REAL NOT NULL, completed REAL);
        ''')

    @contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                yield self.db
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                raise

    def close(self):
        with self.lock:
            self.db.close()
