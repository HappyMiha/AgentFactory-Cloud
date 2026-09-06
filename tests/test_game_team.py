from contextlib import closing
from dataclasses import asdict
from pathlib import Path
import tempfile
import unittest
from agent_factory.storage import SQLiteStorage
from agent_factory.roles import RoleRegistry
from agentfactory_cloud.game_briefs import BriefStore, BriefConflict, FIELDS
from agentfactory_cloud.scope_plans import ScopePlans
from agentfactory_cloud.game_team import GameTeams,role_pack,digest

class GameTeamTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.briefs=BriefStore(Path(self.temp.name));self.plans=ScopePlans(self.briefs);self.teams=GameTeams(self.briefs)
        self.brief=self.briefs.create('A small seed garden.','Creator','create-0001')
    def agree(self):
        p=self.plans.write(self.brief['id'],'Creator',1,'scope-0001')
        return self.plans.write(self.brief['id'],'Creator',1,'agree-0001',ident=p['id'],expected_plan=1,agree=True)
    def counts(self):
        with closing(SQLiteStorage(self.briefs.core_database)) as s:
            return {t:s.db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('workforce_compositions','assignments','leases','attempts')}
    def test_versioned_pack_preserves_core_contract_and_duties(self):
        roles=role_pack();self.assertEqual(len(roles),5)
        self.assertEqual(len({r.id for r in roles}),5)
        self.assertEqual(digest([asdict(r) for r in roles]),digest([asdict(r) for r in role_pack()]))
        with closing(SQLiteStorage(self.briefs.core_database)) as s:
            reg=RoleRegistry(s)
            for r in roles:self.assertEqual(reg.register(r),reg.register(r))
        dev=next(r for r in roles if r.id=='game-developer');self.assertIn('game-qa',dev.incompatible_duties)
    def test_view_has_no_composition_and_missing_scope_blocks_assessment(self):
        before=self.counts();v=self.teams.view(self.brief['id'],'Creator')
        self.assertFalse(v['can_assess']);self.assertEqual(v['planned_tokens'],0)
        self.assertEqual(self.counts(),before)
        with self.assertRaises(BriefConflict):self.teams.assess(self.brief['id'],'Creator',v['snapshot_digest'])
    def test_core_gap_receipt_replays_after_restart_without_execution(self):
        self.agree();v=self.teams.view(self.brief['id'],'Creator');self.assertTrue(v['can_assess'])
        self.assertEqual(sum(r['planned_tokens'] for r in v['roles']),v['planned_tokens'])
        first=self.teams.assess(self.brief['id'],'Creator',v['snapshot_digest'])
        second=GameTeams(BriefStore(self.briefs.folder)).assess(self.brief['id'],'Creator',v['snapshot_digest'])
        self.assertEqual(first,second);self.assertIsNotNone(first['core_assessment'])
        self.assertNotEqual(first['core_assessment']['status'],'ready')
        self.assertEqual(self.counts(),{'workforce_compositions':1,'assignments':0,'leases':0,'attempts':0})
        self.assertFalse(first['execution_ready']);self.assertFalse(first['can_start']);self.assertFalse(first['can_stop'])
        with closing(SQLiteStorage(self.briefs.core_database)) as s:
            rows=s.db.execute('SELECT primary_assignments_json,qualifications_json FROM workforce_role_pools').fetchall()
            self.assertEqual(len(rows),5)
            self.assertTrue(all(r[0]=='[]' and r[1]=='[]' for r in rows))
    def test_changed_scope_or_brief_rejects_old_snapshot(self):
        p=self.agree();v=self.teams.view(self.brief['id'],'Creator')
        self.plans.write(self.brief['id'],'Creator',1,'edit-0001',ident=p['id'],expected_plan=2,scope=p['scope']|{'token_allowance':50000})
        with self.assertRaises(BriefConflict):self.teams.assess(self.brief['id'],'Creator',v['snapshot_digest'])
        self.briefs.save(self.brief['id'],'Creator',1,'brief-edit',{'fields':{k:'Human choice' for k in FIELDS},'questions':[],'assumptions':[]})
        latest=self.teams.view(self.brief['id'],'Creator');self.assertFalse(latest['can_assess']);self.assertEqual(self.counts()['workforce_compositions'],0)
    def test_other_actor_cannot_read_or_assess(self):
        self.agree();v=self.teams.view(self.brief['id'],'Creator')
        for operation in (lambda:self.teams.view(self.brief['id'],'Other'),lambda:self.teams.assess(self.brief['id'],'Other',v['snapshot_digest'])):
            with self.assertRaises(KeyError):operation()
        self.assertEqual(self.counts()['workforce_compositions'],0)
    def test_original_and_scope_unchanged_by_assessment(self):
        p=self.agree();original=self.briefs.get(self.brief['id'],'Creator');v=self.teams.view(self.brief['id'],'Creator')
        self.teams.assess(self.brief['id'],'Creator',v['snapshot_digest'])
        self.assertEqual(self.briefs.get(self.brief['id'],'Creator'),original);self.assertEqual(self.plans.get(p['id'],'Creator'),p)
