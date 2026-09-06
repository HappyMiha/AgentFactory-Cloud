"""Opt-in actual PostgreSQL qualification; creates only disposable test databases."""
import json
from contextlib import closing
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))


@unittest.skipUnless(os.environ.get('CLOUD_POSTGRES_ADMIN_JSON'), 'Actual isolated PostgreSQL configuration required')
class HostedStoreTests(unittest.TestCase):
    def setUp(self):
        import psycopg
        from psycopg import sql
        from agentfactory_cloud.hosted_store import HostedStore, TenantContext, migrate, grant_runtime
        self.pg,self.sql=psycopg,sql
        config=json.loads(Path(os.environ['CLOUD_POSTGRES_ADMIN_JSON']).read_text(encoding='utf-8'))
        self.admin_info={key:config[key] for key in ('host','port','user','password')}
        if self.admin_info['host'] != '127.0.0.1' or self.admin_info['port'] == 5432:
            raise ValueError('Tests require an explicitly isolated nondefault loopback cluster')
        self.admin=psycopg.connect(**self.admin_info,dbname='postgres',autocommit=True)
        self.addCleanup(self.admin.close)
        self.databases=[]
        self.role='cloud022_test_role_'+uuid.uuid4().hex[:12]
        self.password=secrets.token_urlsafe(32)
        self.admin.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(self.role),sql.Literal(self.password)))
        self.addCleanup(self.cleanup_databases)
        self.database=self.new_database()
        with psycopg.connect(**self.admin_info,dbname=self.database) as db:
            migrate(db);grant_runtime(db,self.role)
        self.runtime_info={**self.admin_info,'user':self.role,'password':self.password,'dbname':self.database}
        self.store=HostedStore(self.runtime_info)
        self.a=TenantContext('tenant-a','creator-a');self.b=TenantContext('tenant-b','creator-b')
        self.folder=tempfile.TemporaryDirectory(dir=os.environ.get('CLOUD_POSTGRES_TEST_WORK'));self.addCleanup(self.folder.cleanup)

    def new_database(self):
        name='cloud022_test_'+uuid.uuid4().hex[:16]
        self.admin.execute(self.sql.SQL('CREATE DATABASE {}').format(self.sql.Identifier(name)))
        self.databases.append(name)
        return name

    def cleanup_databases(self):
        for name in reversed(self.databases):
            if not name.startswith('cloud022_test_'):raise ValueError('Refuse unrelated database cleanup')
            self.admin.execute(self.sql.SQL('DROP DATABASE {} WITH (FORCE)').format(self.sql.Identifier(name)))
        self.admin.execute(self.sql.SQL('DROP ROLE {}').format(self.sql.Identifier(self.role)))

    def put(self,context=None,**changes):
        values={'ident':'source-1','kind':'SourceVersion','identity':{'core_source_id':'source-original','source_sha256':'a'*64},'body':{'state':'available'},'expected_revision':0,'command_id':'create-1'}
        values.update(changes)
        return self.store.put(context or self.a,**values)

    def counts(self):
        with self.pg.connect(**self.admin_info,dbname=self.database) as db:
            return [db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ('cloud_records','cloud_requests','cloud_audit','cloud_outbox')]

    def test_atomic_idempotency_and_conflicting_replay(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        result=self.put();self.assertEqual(self.put(),result);self.assertEqual(self.counts(),[1,1,1,1])
        self.put(body={'state':'archived'},expected_revision=1,command_id='edit-1')
        self.assertEqual(self.put(),result)  # Exact original result, not latest state.
        with self.assertRaises(StoreConflict):self.put(body={'state':'different'})
        self.assertEqual(self.counts(),[1,2,2,2])

    def test_tenant_rls_denies_foreign_reads_writes_and_unset_context(self):
        self.put()
        with self.assertRaises(KeyError):self.store.get(self.b,'source-1')
        with self.store.transaction(self.b) as db:
            self.assertEqual(db.execute('SELECT * FROM cloud_records').fetchall(),[])
        with self.assertRaises(self.pg.Error),self.store.transaction(self.b) as db:
            db.execute("INSERT INTO cloud_records VALUES('tenant-a','foreign','Project',1,'{}','{}')")
        with self.pg.connect(**self.runtime_info) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM cloud_records').fetchone()[0],0)
        self.assertEqual(self.counts(),[1,1,1,1])

    def test_privileged_runtime_role_rejects(self):
        from agentfactory_cloud.hosted_store import HostedStore
        with self.assertRaises(PermissionError):HostedStore({**self.admin_info,'dbname':self.database}).get(self.a,'missing')

    def test_identity_and_audit_are_immutable_even_through_direct_sql(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        self.put()
        with self.assertRaises(StoreConflict):self.put(identity={'core_source_id':'replacement'},expected_revision=1,command_id='replace')
        for statement in ["UPDATE cloud_records SET identity='{}',revision=2",'DELETE FROM cloud_records','UPDATE cloud_audit SET revision=99','DELETE FROM cloud_audit','TRUNCATE cloud_audit',"UPDATE cloud_outbox SET payload='{}'"]:
            with self.subTest(statement=statement),self.assertRaises(self.pg.Error),self.store.transaction(self.a) as db:db.execute(statement)
        self.assertEqual(self.counts(),[1,1,1,1])

    def test_concurrent_revision_writes_have_one_winner(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        self.put()
        def edit(index):
            try:return self.put(expected_revision=1,command_id='edit-'+str(index),body={'state':str(index)})['revision']
            except StoreConflict:return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as workers:self.assertCountEqual(list(workers.map(edit,[1,2])),[2,'conflict'])
        self.assertEqual(self.counts(),[1,2,2,2])

    def test_database_failure_rolls_back_record_audit_and_outbox(self):
        with self.pg.connect(**self.admin_info,dbname=self.database) as db:
            db.execute("CREATE TRIGGER injected_failure BEFORE INSERT ON cloud_outbox FOR EACH ROW EXECUTE FUNCTION cloud_immutable()")
        with self.assertRaises(self.pg.Error):self.put()
        self.assertEqual(self.counts(),[0,0,0,0])

    def test_outbox_retry_retains_event_identity_and_rejects_stale_or_foreign_ack(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        self.put();first=self.store.lease(self.a)
        self.assertIsNone(self.store.lease(self.a));self.assertIsNone(self.store.lease(self.b))
        with self.pg.connect(**self.admin_info,dbname=self.database) as db:db.execute("UPDATE cloud_outbox SET lease_until=clock_timestamp()-interval '1 second'")
        second=self.store.lease(self.a)
        self.assertEqual(first['event'],second['event']);self.assertEqual(second['attempts'],2)
        self.assertNotEqual(first['lease_token'],second['lease_token'])
        for context,token in [(self.a,first['lease_token']),(self.b,second['lease_token'])]:
            with self.assertRaises(StoreConflict):self.store.acknowledge(context,second['event']['event_id'],token)
        self.store.acknowledge(self.a,second['event']['event_id'],second['lease_token'])
        self.assertIsNone(self.store.lease(self.a))

    def test_migration_replay_and_modified_checksum_fail_closed(self):
        from agentfactory_cloud.hosted_store import migrate,StoreConflict
        with self.pg.connect(**self.admin_info,dbname=self.database) as db:migrate(db)
        with self.pg.connect(**self.admin_info,dbname=self.database) as db:db.execute("UPDATE cloud_schema SET digest='bad'")
        with self.assertRaises(StoreConflict),self.pg.connect(**self.admin_info,dbname=self.database) as db:migrate(db)
        with self.assertRaises(StoreConflict):self.put()

    def test_sqlite_snapshot_preserves_revision_identity_and_replay(self):
        from agentfactory_cloud.hosted_store import import_sqlite_snapshot
        path=Path(self.folder.name)/'synthetic.sqlite'
        record={'tenant_id':'tenant-a','id':'build-1','kind':'Build','revision':7,'identity':{'source_version_id':'source-accepted','artifact_sha256':'b'*64},'body':{'state':'ready'}}
        with closing(sqlite3.connect(path)) as db, db:
            db.execute('CREATE TABLE cloud_product_export(document TEXT)');db.execute('INSERT INTO cloud_product_export VALUES(?)',(json.dumps(record),))
        first=import_sqlite_snapshot(self.store,self.a,path)
        self.assertEqual(import_sqlite_snapshot(self.store,self.a,path),first)
        self.assertEqual(self.store.get(self.a,'build-1'),record)
        self.assertEqual(self.counts(),[1,0,1,1])
        with self.assertRaises(ValueError):import_sqlite_snapshot(self.store,self.b,path)

    def test_encrypted_dump_restore_recovers_records_audit_and_pending_delivery(self):
        from cryptography.fernet import Fernet,InvalidToken
        from agentfactory_cloud.hosted_store import HostedStore,grant_runtime
        tools=Path(os.environ['CLOUD_POSTGRES_BIN'])
        self.put();self.store.lease(self.a)
        env={**os.environ,'PGPASSWORD':self.admin_info['password']}
        args=['-h',self.admin_info['host'],'-p',str(self.admin_info['port']),'-U',self.admin_info['user']]
        dump=subprocess.run([str(tools/'pg_dump.exe' if os.name=='nt' else tools/'pg_dump'),*args,'-Fc','--no-owner','--no-acl',self.database],env=env,capture_output=True,check=True,timeout=30).stdout
        cipher=Fernet(Fernet.generate_key());encrypted=cipher.encrypt(dump)
        backup=Path(self.folder.name)/'backup.fernet';backup.write_bytes(encrypted)
        self.assertNotIn(b'source-original',encrypted)
        with self.assertRaises(InvalidToken):Fernet(Fernet.generate_key()).decrypt(encrypted)
        restored=self.new_database()
        subprocess.run([str(tools/'pg_restore.exe' if os.name=='nt' else tools/'pg_restore'),*args,'--exit-on-error','--no-owner','--no-acl','-d',restored],input=cipher.decrypt(backup.read_bytes()),env=env,capture_output=True,check=True,timeout=30)
        with self.pg.connect(**self.admin_info,dbname=restored) as db:grant_runtime(db,self.role)
        recovered=HostedStore({**self.runtime_info,'dbname':restored})
        self.assertEqual(recovered.get(self.a,'source-1'),self.store.get(self.a,'source-1'))
        with self.pg.connect(**self.admin_info,dbname=self.database) as original,self.pg.connect(**self.admin_info,dbname=restored) as target:
            for table in ('cloud_records','cloud_requests','cloud_audit','cloud_outbox','cloud_schema'):
                self.assertEqual(original.execute('SELECT * FROM '+table+' ORDER BY 1,2').fetchall(),target.execute('SELECT * FROM '+table+' ORDER BY 1,2').fetchall())
        with self.assertRaises(KeyError):recovered.get(self.b,'source-1')

    def test_connection_termination_before_commit_leaves_no_state(self):
        with self.assertRaises(self.pg.Error),self.store.transaction(self.a) as db:
            db.execute("INSERT INTO cloud_records VALUES('tenant-a','interrupted','Project',1,'{}','{}')")
            pid=db.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            self.admin.execute('SELECT pg_terminate_backend(%s)',(pid,))
            db.execute('SELECT 1')
        self.assertEqual(self.counts(),[0,0,0,0])

    def test_snapshot_conflict_rolls_back_all_new_records(self):
        from agentfactory_cloud.hosted_store import import_sqlite_snapshot,StoreConflict
        existing=self.put()
        records=[{**existing,'id':'new-before-conflict'}, {**existing,'revision':99}]
        path=Path(self.folder.name)/'conflict.sqlite'
        with closing(sqlite3.connect(path)) as db,db:
            db.execute('CREATE TABLE cloud_product_export(document TEXT)')
            db.executemany('INSERT INTO cloud_product_export VALUES(?)',[(json.dumps(r),) for r in records])
        with self.assertRaises(StoreConflict):import_sqlite_snapshot(self.store,self.a,path)
        self.assertEqual(self.counts(),[1,1,1,1])
        with self.assertRaises(KeyError):self.store.get(self.a,'new-before-conflict')

    def test_schema_metadata_lock_obeys_runtime_timeout(self):
        import time
        self.put()
        blocker=self.pg.connect(**self.admin_info,dbname=self.database)
        workers=ThreadPoolExecutor(max_workers=1)
        try:
            blocker.execute('LOCK TABLE cloud_schema IN ACCESS EXCLUSIVE MODE')
            started=time.monotonic()
            pending=workers.submit(self.store.get,self.a,'source-1')
            with self.assertRaises((self.pg.errors.QueryCanceled,self.pg.errors.LockNotAvailable)):
                pending.result(timeout=8)
            self.assertLess(time.monotonic()-started,8)
        finally:
            blocker.rollback();blocker.close();workers.shutdown(wait=True)
        self.assertEqual(self.store.get(self.a,'source-1')['revision'],1)


if __name__=='__main__':unittest.main()
