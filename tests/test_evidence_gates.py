"""Counterexamples for the synthetic gate policy; no game acceptance is implied."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('evidence_gates', Path(__file__).resolve().parents[1] / 'scripts/validate_evidence_gates.py')
gates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.policy, self.fixtures = gates.load()
        self.bundle = deepcopy(self.fixtures['bundle'])

    def record(self, name):
        return next(r for r in self.bundle['evidence'] if r['check'] == name)

    def evaluate(self):
        return gates.evaluate(self.bundle, self.policy, self.fixtures['now'])['gates']

    def test_all_documented_scenarios(self):
        self.assertEqual(gates.run_scenarios(self.policy, self.fixtures), 13)

    def test_each_gate_has_an_action_and_preserves_subject(self):
        before = deepcopy(self.bundle)
        result = gates.evaluate(self.bundle, self.policy, self.fixtures['now'])
        self.assertEqual(result['subject'], before['subject'])
        self.assertEqual(self.bundle, before)
        self.assertTrue(all(g['allowed'] and g['next_action'] for g in result['gates'].values()))
        self.assertIn('no real checks', result['verification'])

    def test_missing_failed_skipped_and_simulated_playtest_never_allow_play(self):
        for patch in ({'status': 'failed'}, {'status': 'skipped'}, {'status': 'unknown'},
                      {'mode': 'simulation'}, {'level': 'code_check'}):
            with self.subTest(patch=patch):
                self.setUp()
                self.record('playtest').update(patch)
                result = self.evaluate()
                self.assertTrue(result['Ready']['allowed'])
                self.assertTrue(all(not result[name]['allowed'] for name in ('Playable', 'Exportable', 'Publishable', 'Sellable')))
                self.assertTrue(result['Playable']['next_action'])

    def test_every_build_binding_field_invalidates_play_evidence(self):
        original = deepcopy(self.bundle['subject'])
        for key in original:
            with self.subTest(key=key):
                self.bundle['subject'] = deepcopy(original)
                self.bundle['subject'][key] = 2 if key == 'run_attempt' else 'f' * 64 if key.endswith('_sha256') else 'changed-version'
                self.assertFalse(self.evaluate()['Playable']['allowed'])

    def test_ready_does_not_require_a_build_or_commercial_context(self):
        self.bundle['subject'].update(build_id=None, artifact_sha256=None)
        self.bundle['release_context'] = None
        self.bundle['sale_context'] = None
        self.bundle['authorized_owner_id'] = None
        result = self.evaluate()
        self.assertTrue(result['Ready']['allowed'])
        self.assertFalse(result['Playable']['allowed'])

    def test_private_play_does_not_require_a_listing_or_release(self):
        self.bundle['release_context'] = None
        self.bundle['sale_context'] = None
        result = self.evaluate()
        self.assertTrue(result['Playable']['allowed'])
        self.assertTrue(result['Exportable']['allowed'])
        self.assertFalse(result['Publishable']['allowed'])
        self.assertFalse(result['Sellable']['allowed'])

    def test_stale_future_and_timezone_free_proofs_are_blocked(self):
        for patch in ({'expires_at': self.fixtures['now']}, {'checked_at': '2026-09-06T00:00:00Z'},
                      {'checked_at': '2026-09-05T11:00:00'}):
            with self.subTest(patch=patch):
                self.setUp()
                self.record('playtest').update(patch)
                self.assertEqual(self.evaluate()['Playable']['blockers'][0]['reason'], 'stale')

    def test_duplicate_passes_are_not_an_implicit_latest_wins_rule(self):
        self.bundle['evidence'].append(deepcopy(self.record('playtest')))
        self.assertEqual(self.evaluate()['Playable']['blockers'][0]['reason'], 'duplicate')

    def test_wrong_tenant_inactive_or_unqualified_issuer_is_blocked(self):
        for patch in ({'tenant_id': 'other-team'}, {'active': False}, {'roles': ['unrelated-role']}):
            with self.subTest(patch=patch):
                self.setUp()
                self.bundle['trusted_issuers'][self.record('playtest')['issuer_id']].update(patch)
                self.assertEqual(self.evaluate()['Playable']['blockers'][0]['reason'], 'untrusted_issuer')

    def test_rights_for_one_use_do_not_authorize_another(self):
        self.record('sell_rights')['use'] = 'publish'
        result = self.evaluate()
        self.assertTrue(result['Publishable']['allowed'])
        self.assertEqual(result['Sellable']['blockers'][0]['reason'], 'wrong_use')

    def test_reviewer_cannot_be_a_producer(self):
        self.bundle['producer_issuer_ids'].append(self.record('reviewer_approval')['issuer_id'])
        self.assertEqual(self.evaluate()['Publishable']['blockers'][0]['reason'], 'review_conflict')

    def test_different_agent_with_same_producer_model_is_not_independent(self):
        issuer = self.bundle['trusted_issuers'][self.record('reviewer_approval')['issuer_id']]
        issuer['model_identity'] = self.bundle['producer_model_identities'][0]
        self.assertEqual(self.evaluate()['Publishable']['blockers'][0]['reason'], 'review_conflict')

    def test_owner_acceptance_is_human_and_owned_by_authorized_actor(self):
        self.bundle['trusted_issuers'][self.record('owner_acceptance')['issuer_id']]['kind'] = 'service'
        self.assertEqual(self.evaluate()['Publishable']['blockers'][0]['reason'], 'human_required')
        self.setUp()
        self.bundle['authorized_owner_id'] = 'another-owner'
        self.assertEqual(self.evaluate()['Publishable']['blockers'][0]['reason'], 'untrusted_issuer')

    def test_changed_release_terms_require_new_approvals(self):
        for key, value in (('release_revision', 2), ('visibility', 'unlisted'), ('rights_revision', 2),
                           ('moderation_policy_version', 'policy-v2')):
            with self.subTest(key=key):
                self.setUp()
                self.bundle['release_context'][key] = value
                self.assertFalse(self.evaluate()['Publishable']['allowed'])

    def test_changed_offer_only_blocks_sale(self):
        for key, value in (('listing_revision', 2), ('price_minor', 999), ('license_version', 'license-v2'),
                           ('seller_eligibility_revision', 2)):
            with self.subTest(key=key):
                self.setUp()
                self.bundle['sale_context'][key] = value
                result = self.evaluate()
                self.assertTrue(result['Publishable']['allowed'])
                self.assertFalse(result['Sellable']['allowed'])

    def test_free_or_invalid_offer_is_not_sellable_even_with_matching_proofs(self):
        for price in (0, -1, True):
            with self.subTest(price=price):
                self.setUp()
                self.bundle['sale_context']['price_minor'] = price
                for name in ('sell_rights', 'seller_eligibility', 'sale_terms'):
                    self.record(name)['decision_context'] = {**self.bundle['release_context'], **self.bundle['sale_context']}
                self.assertFalse(self.evaluate()['Sellable']['allowed'])

    def test_missing_toolchain_identity_fails_validation(self):
        del self.bundle['subject']['toolchain_sha256']
        with self.assertRaisesRegex(ValueError, 'complete subject'):
            self.evaluate()

    def test_code_check_alone_cannot_make_a_game_ready_or_playable(self):
        self.bundle['evidence'] = [self.record('code')]
        self.assertTrue(all(not result['allowed'] for result in self.evaluate().values()))


if __name__ == '__main__':
    unittest.main()
