"""Cloud account lifecycle and opaque credentials; trusted provisioning, no public signup."""
from dataclasses import dataclass
import hashlib
import hmac
import math
import secrets
import time

from .access import AccessDenied, Principal, Resource, ROLES, permits


def hashed(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def valid_id(value):
    return isinstance(value, str) and 0 < len(value) <= 128 and value.isascii() and all(c.isalnum() or c in '-_:.' for c in value)


def matches(expected, candidate):
    return bool(expected) and isinstance(candidate, str) and len(candidate) <= 256 and hmac.compare_digest(expected, hashed(candidate))


@dataclass(frozen=True)
class Eligibility:
    # Trusted verified eligibility result only; never an HTTP body or inferred age.
    age_band: str
    jurisdiction: str
    provider_route: str
    policy_ref: str


@dataclass(frozen=True)
class AccessPolicy:
    version: str
    expires_at: float
    adult_routes: frozenset[tuple[str, str]] = frozenset()

    def __post_init__(self):
        if (not valid_id(self.version) or type(self.expires_at) not in (int,float)
                or not math.isfinite(self.expires_at) or self.expires_at <= 0
                or not isinstance(self.adult_routes,frozenset)
                or any(not isinstance(route,tuple) or len(route)!=2 or not all(valid_id(x) for x in route) for route in self.adult_routes)):
            raise ValueError('Invalid bounded access policy')

    def eligible(self, account, now):
        return (self.expires_at > now and account['age_band'] == 'adult'
                and account['policy_ref'] == self.version
                and (account['jurisdiction'], account['provider_route']) in self.adult_routes)


class IdentityService:
    def __init__(self, store, *, policy, clock=time.time, session_ttl=900):
        if type(session_ttl) is not int or not 1 <= session_ttl <= 3600:
            raise ValueError('Session lifetime must be between 1 and 3600 seconds')
        self.store, self.policy, self.clock, self.session_ttl = store, policy, clock, session_ttl

    def audit(self, db, account_id, action, outcome):
        db.execute('INSERT INTO identity_audit(account_id,action,outcome,created) VALUES(?,?,?,?)',
                   (account_id, action, outcome, self.clock()))

    def limited(self, action, account_id, client_key):
        if not isinstance(client_key, str) or not 0 < len(client_key) <= 256:
            raise AccessDenied('invalid_client_context', 400)
        now = self.clock()
        # Commit counters even if the following authentication fails. Per-account
        # limits survive client changes; per-peer limits bound invented account IDs.
        with self.store.transaction() as db:
            db.execute('DELETE FROM identity_rates WHERE expires<=?', (now,))
            for scope, value, limit in [('peer', client_key, 40), ('account', account_id, 8)]:
                key=hashed(action+'\0'+scope+'\0'+value)
                existing=db.execute('SELECT count FROM identity_rates WHERE key=?',(key,)).fetchone()
                if not existing and db.execute('SELECT COUNT(*) FROM identity_rates').fetchone()[0] >= 4096:
                    return False
                db.execute('INSERT INTO identity_rates(key,count,expires) VALUES(?,1,?) '
                           'ON CONFLICT(key) DO UPDATE SET count=MIN(count+1,100000)', (key,now+300))
                count=db.execute('SELECT count FROM identity_rates WHERE key=?',(key,)).fetchone()[0]
                if count > limit:
                    if count == limit+1:self.audit(db,None,action,'rate_limited')
                    return False
        return True

    def provision(self, eligibility):
        """Only a trusted verified provisioning integration calls this method."""
        values=(eligibility.age_band, eligibility.jurisdiction, eligibility.provider_route, eligibility.policy_ref)
        if not all(valid_id(v) for v in values):
            raise ValueError('Invalid eligibility record')
        account={'age_band':values[0], 'jurisdiction':values[1], 'provider_route':values[2], 'policy_ref':values[3]}
        if not self.policy.eligible(account,self.clock()):
            raise AccessDenied('access_route_unapproved',403)
        ident=secrets.token_hex(16);login=secrets.token_urlsafe(32);recovery=secrets.token_urlsafe(32)
        with self.store.transaction() as db:
            db.execute('INSERT INTO identity_accounts VALUES(?,?,?,?,?,?,?,?,?)',
                       (ident,'active',hashed(login),hashed(recovery),1,*values))
            self.audit(db,ident,'provision','created')
        return {'account_id':ident,'login_secret':login,'recovery_secret':recovery}

    def membership(self, account_id, tenant_id, roles):
        """Trusted administration only. No client-facing role assignment endpoint."""
        if not valid_id(tenant_id) or not isinstance(roles,(set,frozenset)) or not roles <= ROLES:
            raise ValueError('Invalid tenant role assignment')
        with self.store.transaction() as db:
            account=db.execute('SELECT * FROM identity_accounts WHERE id=?',(account_id,)).fetchone()
            if not account or account['status']!='active':raise AccessDenied()
            db.execute('DELETE FROM identity_memberships WHERE account_id=? AND tenant_id=?',(account_id,tenant_id))
            db.executemany('INSERT INTO identity_memberships VALUES(?,?,?)',[(account_id,tenant_id,r) for r in sorted(roles)])
            self.audit(db,account_id,'membership','changed')

    def login(self, account_id, secret, *, client_key):
        if not valid_id(account_id):raise AccessDenied('authentication_required',401)
        if not self.limited('login',account_id,client_key):raise AccessDenied('rate_limited',429)
        token=None
        with self.store.transaction() as db:
            row=db.execute('SELECT * FROM identity_accounts WHERE id=?',(account_id,)).fetchone()
            if row and row['status']=='active' and self.policy.eligible(row,self.clock()) and matches(row['login_hash'],secret):
                token=secrets.token_urlsafe(32)
                db.execute('DELETE FROM identity_sessions WHERE expires<=?',(self.clock(),))
                # Bound sessions per account without extending an existing session.
                sessions=db.execute('SELECT token_hash FROM identity_sessions WHERE account_id=? ORDER BY expires',(account_id,)).fetchall()
                for old in sessions[:max(0,len(sessions)-7)]:db.execute('DELETE FROM identity_sessions WHERE token_hash=?',(old[0],))
                db.execute('INSERT INTO identity_sessions VALUES(?,?,?,?)',(hashed(token),account_id,row['generation'],self.clock()+self.session_ttl))
            self.audit(db,account_id if row else None,'login','allowed' if token else 'denied')
        if not token:raise AccessDenied('authentication_required',401)
        return token

    def current(self, db, key):
        row=db.execute('SELECT a.*,s.generation session_generation,s.expires FROM identity_sessions s '
                       'JOIN identity_accounts a ON a.id=s.account_id WHERE s.token_hash=?',(key,)).fetchone()
        if (not row or row['status']!='active' or row['expires']<=self.clock()
                or row['generation']!=row['session_generation'] or not self.policy.eligible(row,self.clock())):
            raise AccessDenied('authentication_required',401)
        return row

    def authenticate(self, token):
        if not isinstance(token,str) or not 20 <= len(token) <= 256:raise AccessDenied('authentication_required',401)
        key=hashed(token)
        with self.store.transaction() as db:
            row=self.current(db,key)
            return Principal(row['id'],key,row['generation'])

    def current_principal(self, db, principal):
        if not isinstance(principal, Principal):
            raise AccessDenied('authentication_required', 401)
        row = self.current(db, principal.session_key)
        if row['id'] != principal.account_id or row['generation'] != principal.generation:
            raise AccessDenied('authentication_required', 401)
        return row

    def authorize(self, principal, action, resource):
        if not isinstance(principal,Principal) or not isinstance(resource,Resource):raise AccessDenied()
        with self.store.transaction() as db:
            row=self.current_principal(db,principal)
            roles={r[0] for r in db.execute('SELECT role FROM identity_memberships WHERE account_id=? AND tenant_id=?',
                                          (row['id'],resource.tenant_id))}
            allowed=permits(roles,row['id'],action,resource)
            self.audit(db,row['id'],'authorize','allowed' if allowed else 'denied')
        if not allowed:raise AccessDenied()
        return True

    def logout(self, principal, *, client_key):
        if not self.limited('logout',principal.account_id,client_key):raise AccessDenied('rate_limited',429)
        with self.store.transaction() as db:
            self.current_principal(db,principal)
            db.execute('DELETE FROM identity_sessions WHERE token_hash=?',(principal.session_key,))
            self.audit(db,principal.account_id,'logout','revoked')

    def recover(self, account_id, recovery_secret, *, client_key):
        if not valid_id(account_id):raise AccessDenied('authentication_required',401)
        if not self.limited('recover',account_id,client_key):raise AccessDenied('rate_limited',429)
        result=None
        with self.store.transaction() as db:
            row=db.execute('SELECT * FROM identity_accounts WHERE id=?',(account_id,)).fetchone()
            if row and row['status']=='active' and self.policy.eligible(row,self.clock()) and matches(row['recovery_hash'],recovery_secret):
                login=secrets.token_urlsafe(32);recovery=secrets.token_urlsafe(32)
                db.execute('UPDATE identity_accounts SET login_hash=?,recovery_hash=?,generation=generation+1 WHERE id=?',
                           (hashed(login),hashed(recovery),account_id))
                db.execute('DELETE FROM identity_sessions WHERE account_id=?',(account_id,))
                result={'login_secret':login,'recovery_secret':recovery}
            self.audit(db,account_id if row else None,'recover','rotated' if result else 'denied')
        if result is None:raise AccessDenied('authentication_required',401)
        return result

    def request_deletion(self, principal, login_secret, *, client_key):
        if not self.limited('delete',principal.account_id,client_key):raise AccessDenied('rate_limited',429)
        allowed=False
        with self.store.transaction() as db:
            row=self.current_principal(db,principal)
            if matches(row['login_hash'],login_secret):
                allowed=True
                db.execute("UPDATE identity_accounts SET status='deletion_pending',login_hash=NULL,recovery_hash=NULL,generation=generation+1 WHERE id=?",(row['id'],))
                db.execute('DELETE FROM identity_sessions WHERE account_id=?',(row['id'],))
                db.execute('DELETE FROM identity_memberships WHERE account_id=?',(row['id'],))
                db.execute("INSERT INTO identity_deletions VALUES(?,'pending',?,NULL)",(row['id'],self.clock()))
            self.audit(db,row['id'],'delete','pending' if allowed else 'denied')
        if not allowed:raise AccessDenied('authentication_required',401)
        return {'status':'deletion_pending'}

    def finish_deletion(self, account_id, erase_owned_resources):
        """Trusted worker invokes an idempotent eraser; failure keeps a durable pending job."""
        with self.store.transaction() as db:
            row=db.execute('SELECT status FROM identity_deletions WHERE account_id=?',(account_id,)).fetchone()
            if not row:raise AccessDenied()
            if row['status']=='complete':return
        if erase_owned_resources(account_id) is not True:
            raise RuntimeError('Resource erasure did not return verified completion')
        with self.store.transaction() as db:
            db.execute("UPDATE identity_accounts SET status='deleted',age_band='',jurisdiction='',provider_route='',policy_ref='' WHERE id=?",(account_id,))
            db.execute("UPDATE identity_deletions SET status='complete',completed=? WHERE account_id=?",(self.clock(),account_id))
            self.audit(db,account_id,'delete','complete')
