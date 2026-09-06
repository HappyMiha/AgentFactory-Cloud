"""Negative tenancy/lifecycle tests with synthetic identities, no real users."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import tempfile
import unittest
from agentfactory_cloud.identity_store import IdentityStore
from agentfactory_cloud.identity import IdentityService, AccessPolicy, Eligibility
from agentfactory_cloud.access import AccessDenied, Resource


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=IdentityStore(Path(self.temp.name)/'identity.db');self.addCleanup(self.store.close)
        self.now=[1000.0]
        self.policy=AccessPolicy('synthetic-v1',10000,frozenset({('test-region','test-provider')}))
        self.service=IdentityService(self.store,policy=self.policy,clock=lambda:self.now[0])
        self.eligibility=Eligibility('adult','test-region','test-provider','synthetic-v1')
        self.a=self.service.provision(self.eligibility);self.b=self.service.provision(self.eligibility)
        self.service.membership(self.a['account_id'],'tenant-a',{'Creator'})
        self.service.membership(self.b['account_id'],'tenant-b',{'Admin'})
        self.token=self.service.login(self.a['account_id'],self.a['login_secret'],client_key='test-peer')
        self.principal=self.service.authenticate(self.token)

    def resource(self,kind='project',**changes):
        return Resource(**({'tenant_id':'tenant-a','owner_id':self.a['account_id'],'kind':kind}|changes))

    def test_cross_tenant_reads_writes_and_privileged_resources_deny(self):
        for kind in ('project','artifact','worker_result','preview','build','moderation','support'):
            for action in ('read','write','play','moderate','support_read'):
                with self.subTest(kind=kind,action=action),self.assertRaises(AccessDenied):
                    self.service.authorize(self.principal,action,self.resource(kind,tenant_id='tenant-b',owner_id=self.b['account_id']))

    def test_grant_in_one_tenant_does_not_leak_to_second_membership(self):
        self.service.membership(self.a['account_id'],'tenant-b',{'Player'})
        with self.assertRaises(AccessDenied):self.service.authorize(self.principal,'write',self.resource(tenant_id='tenant-b'))
        self.assertTrue(self.service.authorize(self.principal,'play',self.resource('build',tenant_id='tenant-b',visibility='public')))

    def test_role_matrix_and_owner_boundary(self):
        cases=[('Creator','project','read',True),('Player','artifact','read',False),('Player','build','play',True),
               ('Moderator','moderation','moderate',True),('Moderator','artifact','read',False),
               ('Support','support','support_read',True),('Support','project','read',False),('Admin','project','write',True)]
        for role,kind,action,allowed in cases:
            with self.subTest(role=role,kind=kind):
                self.service.membership(self.a['account_id'],'tenant-a',{role})
                resource=self.resource(kind,visibility='public',redacted=True,support_accounts=frozenset({self.a['account_id']}))
                if allowed:self.assertTrue(self.service.authorize(self.principal,action,resource))
                else:
                    with self.assertRaises(AccessDenied):self.service.authorize(self.principal,action,resource)
        self.service.membership(self.a['account_id'],'tenant-a',{'Creator'})
        with self.assertRaises(AccessDenied):self.service.authorize(self.principal,'read',self.resource(owner_id=self.b['account_id']))

    def test_support_needs_redaction_and_target_ticket_grant(self):
        self.service.membership(self.a['account_id'],'tenant-a',{'Support'})
        for resource in [self.resource('support',redacted=True),self.resource('support',support_accounts=frozenset({self.a['account_id']}))]:
            with self.assertRaises(AccessDenied):self.service.authorize(self.principal,'support_read',resource)

    def test_membership_revocation_affects_existing_principal_immediately(self):
        self.service.membership(self.a['account_id'],'tenant-a',set())
        with self.assertRaises(AccessDenied):self.service.authorize(self.principal,'read',self.resource())

    def test_unknown_actions_and_private_player_content_deny(self):
        with self.assertRaises(AccessDenied):self.service.authorize(self.principal,'spend',self.resource())
        self.service.membership(self.a['account_id'],'tenant-a',{'Player'})
        with self.assertRaises(AccessDenied):self.service.authorize(self.principal,'play',self.resource('build'))

    def test_sessions_expire_and_logout_blocks_replay(self):
        self.now[0]+=901
        with self.assertRaises(AccessDenied):self.service.authenticate(self.token)
        self.now[0]=1000;self.service.logout(self.principal,client_key='test-peer')
        with self.assertRaises(AccessDenied):self.service.authenticate(self.token)

    def test_recovery_rotates_both_factors_and_revokes_all_sessions(self):
        result=self.service.recover(self.a['account_id'],self.a['recovery_secret'],client_key='test-peer')
        for operation in [lambda:self.service.authenticate(self.token),lambda:self.service.recover(self.a['account_id'],self.a['recovery_secret'],client_key='test-peer'),
                          lambda:self.service.login(self.a['account_id'],self.a['login_secret'],client_key='test-peer')]:
            with self.assertRaises(AccessDenied):operation()
        fresh=self.service.login(self.a['account_id'],result['login_secret'],client_key='test-peer')
        self.assertEqual(self.service.authenticate(fresh).account_id,self.a['account_id'])

    def test_failed_recovery_cannot_revoke_valid_session(self):
        with self.assertRaises(AccessDenied):self.service.recover(self.a['account_id'],'wrong',client_key='test-peer')
        self.service.authenticate(self.token)

    def test_attempts_are_durable_and_do_not_rollback_on_failure(self):
        for i in range(8):
            with self.assertRaises(AccessDenied):self.service.recover(self.a['account_id'],'wrong',client_key='peer-'+str(i))
        with self.assertRaises(AccessDenied) as error:self.service.recover(self.a['account_id'],self.a['recovery_secret'],client_key='new-peer')
        self.assertEqual(error.exception.status,429)
        self.now[0]+=301
        self.service.recover(self.a['account_id'],self.a['recovery_secret'],client_key='new-peer')

    def test_peer_limit_bounds_invented_accounts(self):
        for i in range(100):
            with self.assertRaises(AccessDenied):self.service.login('invented-'+str(i),'wrong',client_key='one-peer')
        self.assertLess(self.store.db.execute('SELECT COUNT(*) FROM identity_rates').fetchone()[0],50)

    def test_pending_deletion_denies_sessions_recovery_and_clears_factors(self):
        result=self.service.request_deletion(self.principal,self.a['login_secret'],client_key='test-peer')
        self.assertEqual(result['status'],'deletion_pending')
        with self.assertRaises(AccessDenied):self.service.authenticate(self.token)
        with self.assertRaises(AccessDenied):self.service.recover(self.a['account_id'],self.a['recovery_secret'],client_key='test-peer')
        row=self.store.db.execute('SELECT * FROM identity_accounts WHERE id=?',(self.a['account_id'],)).fetchone()
        self.assertIsNone(row['login_hash']);self.assertIsNone(row['recovery_hash'])
        with self.assertRaises(RuntimeError):self.service.finish_deletion(self.a['account_id'],lambda _:False)
        self.assertEqual(self.store.db.execute('SELECT status FROM identity_deletions').fetchone()[0],'pending')
        calls=[]
        def erase(ident):calls.append(ident);return True
        self.service.finish_deletion(self.a['account_id'],erase);self.service.finish_deletion(self.a['account_id'],erase)
        self.assertEqual(calls,[self.a['account_id']])
        self.assertEqual(self.store.db.execute('SELECT status FROM identity_accounts WHERE id=?',(self.b['account_id'],)).fetchone()[0],'active')

    def test_wrong_deletion_factor_does_not_delete_account(self):
        with self.assertRaises(AccessDenied):self.service.request_deletion(self.principal,'wrong',client_key='test-peer')
        self.service.authenticate(self.token)

    def test_age_provider_policy_and_expiry_fail_closed(self):
        for age,region,provider in [('teen','test-region','test-provider'),('under12','test-region','test-provider'),('unknown','test-region','test-provider'),('adult','other','test-provider'),('adult','test-region','other')]:
            with self.subTest(age=age,region=region),self.assertRaises(AccessDenied):self.service.provision(Eligibility(age,region,provider,'synthetic-v1'))
        self.service.policy=AccessPolicy('revoked',10000,self.policy.adult_routes)
        with self.assertRaises(AccessDenied):self.service.authenticate(self.token)
        self.service.policy=self.policy;self.now[0]=10001
        with self.assertRaises(AccessDenied):self.service.authenticate(self.token)

    def test_store_and_audit_never_contain_raw_credentials(self):
        dump='\n'.join(self.store.db.iterdump())
        for secret in [self.a['login_secret'],self.a['recovery_secret'],self.token]:self.assertNotIn(secret,dump)
        self.assertNotIn(self.token,repr(self.principal))

    def test_sessions_survive_reopen_but_check_current_policy(self):
        other=IdentityStore(self.store.path)
        try:
            service=IdentityService(other,policy=self.policy,clock=lambda:self.now[0])
            self.assertEqual(service.authenticate(self.token).account_id,self.a['account_id'])
        finally:other.close()


    def test_every_role_stays_inside_current_tenant(self):
        for role in ('Creator','Player','Moderator','Support','Admin'):
            self.service.membership(self.a['account_id'],'tenant-a',{role})
            for kind in ('artifact','worker_result','preview','support'):
                with self.subTest(role=role,kind=kind),self.assertRaises(AccessDenied):
                    self.service.authorize(self.principal,'read',self.resource(kind,tenant_id='tenant-b',visibility='public',redacted=True))

    def test_policy_lifetime_is_finite_and_unknown_roles_reject(self):
        for expiry in (float('inf'),float('nan'),True,0):
            with self.assertRaises(ValueError):AccessPolicy('test',expiry)
        with self.assertRaises(ValueError):self.service.membership(self.a['account_id'],'tenant-a',{'SuperUser'})

    def test_admin_cannot_read_unredacted_support_payload_via_generic_read(self):
        self.service.membership(self.a['account_id'],'tenant-a',{'Admin'})
        for action in ('read','support_read'):
            with self.assertRaises(AccessDenied):self.service.authorize(self.principal,action,self.resource('support'))


    def test_concurrent_recovery_has_only_one_winner_across_connections(self):
        from concurrent.futures import ThreadPoolExecutor
        other=IdentityStore(self.store.path)
        second=IdentityService(other,policy=self.policy,clock=lambda:self.now[0])
        def attempt(service):
            try:
                service.recover(self.a['account_id'],self.a['recovery_secret'],client_key='parallel-peer')
                return 'rotated'
            except AccessDenied:return 'denied'
        try:
            with ThreadPoolExecutor(max_workers=2) as workers:
                results=list(workers.map(attempt,[self.service,second]))
            self.assertEqual(sorted(results),['denied','rotated'])
            with self.assertRaises(AccessDenied):self.service.authenticate(self.token)
        finally:other.close()

    def test_session_count_is_bounded(self):
        self.service.session_ttl=3600
        for _ in range(10):
            self.now[0]+=301
            self.service.login(self.a['account_id'],self.a['login_secret'],client_key='peer')
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM identity_sessions WHERE account_id=?',(self.a['account_id'],)).fetchone()[0],8)



    def test_mismatched_principal_cannot_mutate_account_or_session(self):
        from dataclasses import replace
        wrong = replace(self.principal, account_id=self.b['account_id'])
        with self.assertRaises(AccessDenied):
            self.service.logout(wrong, client_key='test-peer')
        with self.assertRaises(AccessDenied):
            self.service.request_deletion(wrong, self.a['login_secret'], client_key='test-peer')
        self.assertEqual(self.service.authenticate(self.token), self.principal)
        self.assertTrue(self.service.authorize(self.principal, 'read', self.resource()))

    def test_unpaired_surrogate_credentials_fail_closed_without_revocation(self):
        from agentfactory_cloud.identity import matches
        for secret in ('\ud800', '\udfff', 'valid-prefix' + '\ud800'):
            self.assertFalse(matches('a' * 64, secret))
            with self.assertRaises(AccessDenied):
                self.service.login(self.a['account_id'], secret, client_key='peer')
            with self.assertRaises(AccessDenied):
                self.service.recover(self.a['account_id'], secret, client_key='peer')
            with self.assertRaises(AccessDenied):
                self.service.request_deletion(self.principal, secret, client_key='peer')
            with self.assertRaises(AccessDenied):
                self.service.authenticate('x' * 24 + secret)
        self.assertEqual(self.service.authenticate(self.token), self.principal)
        renewed = self.service.login(self.a['account_id'], self.a['login_secret'], client_key='peer')
        self.assertEqual(self.service.authenticate(renewed).account_id, self.a['account_id'])
        self.assertIn('login_secret', self.service.recover(self.a['account_id'], self.a['recovery_secret'], client_key='peer'))


if __name__=='__main__':unittest.main()
