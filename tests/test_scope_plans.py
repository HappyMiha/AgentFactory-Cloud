"""Real scope persistence and decisions using explicit synthetic planning inputs."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from agentfactory_cloud.game_briefs import BriefStore, BriefConflict, FIELDS
from agentfactory_cloud.scope_plans import ScopePlans, evaluate


class ScopePlanTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.briefs = BriefStore(Path(self.folder.name)); self.plans = ScopePlans(self.briefs)
        self.brief = self.briefs.create('A small game about collecting seeds.', 'Creator', 'brief-0001')

    def create(self):
        return self.plans.write(self.brief['id'], 'Creator', 1, 'scope-0001')

    def edit_brief(self):
        return self.briefs.save(self.brief['id'], 'Creator', 1, 'brief-edit',
            {'fields': {key: 'Human choice' for key in FIELDS}, 'questions': [], 'assumptions': []})

    def test_small_scope_has_leaf_tasks_game_checks_budget_and_no_execution(self):
        plan = self.create()
        self.assertEqual(len(plan['leaf_tasks']), 6)
        self.assertIn(plan['scope']['goal'], ' '.join(plan['leaf_tasks'][2]['acceptance']))
        self.assertEqual(plan['leaf_tasks'][0]['depends_on'], [])
        ids = set()
        for task in plan['leaf_tasks']:
            self.assertTrue(set(task['depends_on']) <= ids); ids.add(task['id'])
        self.assertTrue(plan['scope_agreement_available']); self.assertFalse(plan['execution_ready'])
        self.assertFalse(plan['budget']['usage_measured']); self.assertFalse(plan['budget']['execution_budget_grant'])
        self.assertEqual(self.briefs.get(self.brief['id'], 'Creator'), self.brief)

    def test_large_unsupported_vision_keeps_source_and_requires_explicit_alternative(self):
        original = 'Хочу Unreal MMORPG з відкритим світом, multiplayer та AAA графікою.'
        brief = self.briefs.create(original, 'Creator', 'brief-0002')
        plan = self.plans.write(brief['id'], 'Creator', 1, 'scope-0002')
        self.assertEqual(plan['scope']['engine'], 'unreal')
        self.assertIn('one small room', plan['scope']['goal'])
        self.assertTrue(plan['scope']['deferred_roadmap']); self.assertTrue(plan['scope']['exclusions'])
        self.assertIn('multiplayer session', plan['scope']['deferred_roadmap'])
        self.assertIn('Qualify Unreal', plan['scope']['deferred_roadmap'])
        self.assertFalse(plan['scope_agreement_available'])
        with self.assertRaises(ValueError):
            self.plans.write(brief['id'], 'Creator', 1, 'agree-0001', ident=plan['id'], expected_plan=1, agree=True)
        self.assertEqual(self.briefs.get(brief['id'], 'Creator')['original_text'], original)
        scope = deepcopy(plan['scope']); scope['engine'] = 'godot'
        updated = self.plans.write(brief['id'], 'Creator', 1, 'edit-0001', ident=plan['id'], expected_plan=1, scope=scope)
        self.assertTrue(updated['scope_agreement_available'])

    def test_insufficient_budget_and_unreduced_goal_block_agreement(self):
        scope = self.create()['scope']; scope['token_allowance'] = 1000
        self.assertFalse(evaluate(scope)['scope_agreement_available'])
        scope['token_allowance'] = 40000; scope['goal'] = 'Build an AAA multiplayer open-world game'
        self.assertFalse(evaluate(scope)['scope_agreement_available'])

    def test_unsupported_or_malformed_scope_never_saves(self):
        plan = self.create()
        for change in ({'engine': []}, {'target': 'console'}, {'token_allowance': True}, {'token_allowance': 1.5}, {'goal': '\ud800'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.plans.write(self.brief['id'], 'Creator', 1, 'bad-edit-1', ident=plan['id'], expected_plan=1,
                                 scope=plan['scope'] | change)
        self.assertEqual(self.plans.get(plan['id'], 'Creator')['revision'], 1)

    def test_other_actor_and_other_brief_cannot_use_plan(self):
        plan = self.create()
        with self.assertRaises(KeyError): self.plans.get(plan['id'], 'Other')
        other = self.briefs.create('Another idea', 'Creator', 'brief-0002')
        with self.assertRaises(KeyError):
            self.plans.write(other['id'], 'Creator', 1, 'wrong-id-1', ident=plan['id'], expected_plan=1, scope=plan['scope'])

    def test_conflicting_edit_saves_only_one_version(self):
        plan = self.create()
        def edit(number):
            try:
                return self.plans.write(self.brief['id'], 'Creator', 1, f'edit-000{number}',
                                       ident=plan['id'], expected_plan=1, scope=plan['scope'])['revision']
            except BriefConflict:
                return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(edit, (1, 2))), [2, 'conflict'])

    def test_changed_brief_invalidates_old_plan_without_rewriting_it(self):
        plan = self.create(); self.edit_brief()
        self.assertTrue(self.plans.get(plan['id'], 'Creator')['stale'])
        with self.assertRaises(BriefConflict):
            self.plans.write(self.brief['id'], 'Creator', 1, 'agree-0001', ident=plan['id'], expected_plan=1, agree=True)
        fresh = self.plans.write(self.brief['id'], 'Creator', 2, 'scope-0002')
        self.assertEqual(fresh['id'], plan['id']); self.assertEqual(fresh['revision'], 2)
        self.assertEqual(self.plans.get(plan['id'], 'Creator', revision=1)['scope'], plan['scope'])

    def test_agreement_is_versioned_idempotent_and_never_grants_development(self):
        plan = self.create()
        agreed = self.plans.write(self.brief['id'], 'Creator', 1, 'agree-0001', ident=plan['id'], expected_plan=1, agree=True)
        replay = self.plans.write(self.brief['id'], 'Creator', 1, 'agree-0001', ident=plan['id'], expected_plan=1, agree=True)
        self.assertEqual(agreed, replay); self.assertEqual(agreed['agreement']['reviewed_plan_revision'], 1)
        self.assertFalse(agreed['agreement']['execution_authority'])
        self.assertEqual(self.plans.get(plan['id'], 'Creator', revision=1)['state'], 'draft')
        with closing(sqlite3.connect(self.briefs.core_database)) as db:
            self.assertEqual(db.execute('SELECT phase FROM autonomous_missions').fetchone()[0], 'DRAFT')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM autonomous_backlog_approvals').fetchone()[0], 0)
        with closing(self.briefs.connect()) as db:
            with self.assertRaises(sqlite3.IntegrityError): db.execute("UPDATE scope_versions SET document='{}'")
        reopened = ScopePlans(BriefStore(Path(self.folder.name)))
        self.assertEqual(reopened.get(plan['id'], 'Creator'), agreed)


if __name__ == '__main__': unittest.main()
