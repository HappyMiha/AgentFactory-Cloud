"""HTTP boundary conformance with disposable synthetic accounts/resources."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import tempfile
import unittest
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from agentfactory_cloud.identity_store import IdentityStore
from agentfactory_cloud.identity import IdentityService, AccessPolicy, Eligibility
from agentfactory_cloud.identity_api import identity_router
from agentfactory_cloud.access import AccessDenied, Resource


class IdentityAPITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=IdentityStore(Path(self.temp.name)/'accounts.db');self.addCleanup(self.store.close)
        self.now=[1000.0]
        self.service=IdentityService(self.store,policy=AccessPolicy('test-v1',10000,frozenset({('test','test')})),clock=lambda:self.now[0])
        self.a=self.service.provision(Eligibility('adult','test','test','test-v1'))
        self.b=self.service.provision(Eligibility('adult','test','test','test-v1'))
        self.service.membership(self.a['account_id'],'a',{'Creator'})
        self.service.membership(self.b['account_id'],'b',{'Admin'})
        self.app=FastAPI();self.app.include_router(identity_router(self.service))
        resources={'owned':Resource('a',self.a['account_id'],'artifact'),'foreign':Resource('b',self.b['account_id'],'worker_result')}
        @self.app.get('/test-resources/{identity}')
        def resource(identity:str,request:Request):
            try:
                token=request.headers.get('authorization','').removeprefix('Bearer ')
                principal=self.service.authenticate(token)
                found=resources.get(identity)
                if found is None:raise AccessDenied()
                self.service.authorize(principal,'read',found)
                return {'id':identity}
            except AccessDenied as error:raise HTTPException(error.status,detail={'code':error.code}) from None
        self.client=TestClient(self.app);self.addCleanup(self.client.close)

    def login(self):
        response=self.client.post('/identity/sessions',json={'account_id':self.a['account_id'],'secret':self.a['login_secret']})
        self.assertEqual(response.status_code,200,response.text)
        return {'Authorization':'Bearer '+response.json()['access_token']}

    def test_login_read_logout_and_replay(self):
        headers=self.login()
        response=self.client.get('/identity/session',headers=headers)
        self.assertEqual(response.status_code,200);self.assertEqual(response.headers['cache-control'],'no-store')
        self.assertNotIn(headers['Authorization'],response.text)
        self.assertEqual(self.client.delete('/identity/session',headers=headers).status_code,204)
        self.assertEqual(self.client.get('/identity/session',headers=headers).status_code,401)

    def test_foreign_and_missing_resources_are_indistinguishable(self):
        headers=self.login()
        self.assertEqual(self.client.get('/test-resources/owned',headers=headers).status_code,200)
        foreign=self.client.get('/test-resources/foreign',headers=headers);missing=self.client.get('/test-resources/missing',headers=headers)
        self.assertEqual(foreign.status_code,404);self.assertEqual(foreign.json(),missing.json())

    def test_client_identity_roles_and_tenants_are_rejected(self):
        for field in ('actor','roles','tenant_id','age_band','policy_ref'):
            with self.subTest(field=field):
                response=self.client.post('/identity/sessions',json={'account_id':self.a['account_id'],'secret':self.a['login_secret'],field:'Admin'})
                self.assertEqual(response.status_code,400);self.assertNotIn(self.a['login_secret'],response.text)

    def test_malformed_and_oversized_credentials_are_never_echoed(self):
        for payload in [{'account_id':self.a['account_id'],'secret':{'private':'do-not-echo'}}, {'secret':'do-not-echo'},['do-not-echo']]:
            response=self.client.post('/identity/sessions',json=payload)
            self.assertEqual(response.status_code,400);self.assertNotIn('do-not-echo',response.text)
            self.assertEqual(response.headers['cache-control'],'no-store')
        self.assertEqual(self.client.post('/identity/sessions',content='x'*4097).status_code,400)
        self.assertEqual(self.client.post('/identity/sessions',content='{"secret":"one","secret":"two","account_id":"a"}').status_code,400)

    def test_expiry_and_bad_explicit_auth_reject(self):
        headers=self.login();self.now[0]+=901
        self.assertEqual(self.client.get('/identity/session',headers=headers).status_code,401)
        self.assertEqual(self.client.get('/identity/session',headers={'Authorization':'wrong'}).status_code,401)
        self.assertEqual(self.client.get('/identity/session',headers=[('Authorization','Bearer a'),('Authorization','Bearer b')]).status_code,401)

    def test_recovery_is_single_use_and_revokes_previous_session(self):
        headers=self.login()
        response=self.client.post('/identity/recovery',json={'account_id':self.a['account_id'],'secret':self.a['recovery_secret']})
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.get('/identity/session',headers=headers).status_code,401)
        self.assertEqual(self.client.post('/identity/recovery',json={'account_id':self.a['account_id'],'secret':self.a['recovery_secret']}).status_code,401)
        self.assertEqual(self.client.post('/identity/sessions',json={'account_id':self.a['account_id'],'secret':response.json()['login_secret']}).status_code,200)

    def test_deletion_requires_reauthentication_and_two_confirmations(self):
        headers=self.login();body={'login_secret':self.a['login_secret'],'confirmed':True}
        self.assertEqual(self.client.post('/identity/account/deletion',headers=headers,json=body).status_code,400)
        response=self.client.post('/identity/account/deletion',headers=headers|{'X-Identity-Confirm':'true'},json=body|{'confirmed':'true'})
        self.assertEqual(response.status_code,400)
        response=self.client.post('/identity/account/deletion',headers=headers|{'X-Identity-Confirm':'true'},json=body)
        self.assertEqual(response.status_code,202);self.assertEqual(response.json()['status'],'deletion_pending')
        self.assertEqual(self.client.get('/identity/session',headers=headers).status_code,401)
        self.assertEqual(self.store.db.execute('SELECT status FROM identity_deletions').fetchone()[0],'pending')

    def test_rate_limits_survive_forwarded_header_changes(self):
        for i in range(8):
            response=self.client.post('/identity/recovery',headers={'X-Forwarded-For':str(i)},json={'account_id':self.a['account_id'],'secret':'wrong'})
            self.assertEqual(response.status_code,401)
        response=self.client.post('/identity/recovery',json={'account_id':self.a['account_id'],'secret':self.a['recovery_secret']})
        self.assertEqual(response.status_code,429)
        self.assertTrue(self.store.db.execute("SELECT 1 FROM identity_audit WHERE outcome='rate_limited'").fetchone())

    def test_no_public_signup_policy_override_or_hosted_brief_route(self):
        self.assertEqual(self.client.post('/identity/accounts',json={'age_band':'adult','role':'Admin'}).status_code,404)
        self.assertEqual(self.client.post('/briefs',json={'owner':self.a['account_id']}).status_code,404)
        self.service.policy=AccessPolicy('none',10000)
        self.assertEqual(self.client.post('/identity/sessions',json={'account_id':self.a['account_id'],'secret':self.a['login_secret']}).status_code,401)


if __name__=='__main__':unittest.main()
