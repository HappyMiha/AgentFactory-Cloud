"""Regression checks for false evidence, duplicate ownership and release cycles."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('upstream_validator', ROOT / 'scripts/validate_upstream_map.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class UpstreamMapTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'docs/upstream-capability-map.json').read_text(encoding='utf-8'))
        self.cloud = json.loads((ROOT / 'examples/agentfactory-cloud-backlog.json').read_text(encoding='utf-8'))

    def check(self):
        return validator.validate(self.data, self.cloud)

    def test_complete_map_passes_without_claiming_product_acceptance(self):
        self.assertIn('67 Cloud capabilities, 42 upstream tasks; no product gate accepted', self.check())

    def test_missing_or_duplicate_task_is_rejected(self):
        for field in ['capabilities', 'upstream_tasks']:
            with self.subTest(field=field):
                original = copy.deepcopy(self.data[field])
                self.data[field].pop()
                with self.assertRaisesRegex(validator.MapError, 'Expected all'): self.check()
                self.data[field] = original + [copy.deepcopy(original[0])]
                with self.assertRaisesRegex(validator.MapError, 'duplicate'): self.check()
                self.data[field] = original

    def test_floating_or_mismatched_version_is_rejected(self):
        self.data['baseline']['core']['commit'] = 'main'
        with self.assertRaisesRegex(validator.MapError, 'full commit'): self.check()
        self.setUp()
        self.data['capabilities'][0]['core_version'] = 'a' * 40
        with self.assertRaisesRegex(validator.MapError, 'version mismatch'): self.check()

    def test_source_presence_cannot_become_verified_product(self):
        self.data['capabilities'][0]['qualification'] = 'verified'
        with self.assertRaisesRegex(validator.MapError, 'separately accepted integration evidence'): self.check()

    def test_planned_upstream_cannot_be_marked_merged_from_audit(self):
        self.data['upstream_tasks'][1]['engineering_status'] = 'merged'
        with self.assertRaisesRegex(validator.MapError, 'lacks accepted engineering evidence'): self.check()

    def test_unrelated_merged_review_cannot_complete_another_requirement(self):
        self.data['upstream_tasks'][1]['engineering_status'] = 'merged'
        self.data['upstream_tasks'][1]['evidence'] = ['ci-merged']
        with self.assertRaisesRegex(validator.MapError, 'lacks accepted engineering evidence'): self.check()

    def test_shared_owner_and_missing_integration_scenario_are_rejected(self):
        self.data['capabilities'][0]['implementation_owner'] = ['Core', 'Cloud.Games']
        with self.assertRaisesRegex(validator.MapError, 'one implementation owner'): self.check()
        self.setUp()
        self.data['capabilities'][0]['integration_test']['scenario'] = ''
        with self.assertRaisesRegex(validator.MapError, 'integration test required'): self.check()

    def test_unknown_evidence_and_source_escape_are_rejected(self):
        self.data['capabilities'][0]['evidence'] = ['unknown']
        with self.assertRaisesRegex(validator.MapError, 'unknown evidence'): self.check()
        self.setUp()
        self.data['evidence_catalog'][0]['paths'] = ['../private.txt']
        with self.assertRaisesRegex(validator.MapError, 'unsafe source path'): self.check()

    def test_foreign_requirement_is_not_an_executable_dependency(self):
        self.data['capabilities'][0]['dependencies'] = ['AF-GC-026']
        with self.assertRaisesRegex(validator.MapError, 'foreign or unknown scheduling dependency'): self.check()

    def test_reverse_traceability_must_match_forward_links(self):
        self.data['upstream_tasks'][0]['cloud_consumers'] = []
        with self.assertRaisesRegex(validator.MapError, 'reverse traceability mismatch'): self.check()

    def test_journey_mapping_cannot_create_circular_cross_repo_gate(self):
        self.data['journey_links'][0]['scheduling_dependency'] = True
        with self.assertRaisesRegex(validator.MapError, 'must not become a scheduling prerequisite'): self.check()

    def set_dependency(self, task, dependencies):
        next(c for c in self.data['capabilities'] if c['id'] == task)['dependencies'] = dependencies
        next(c for c in self.cloud['items'] if c['stable_id'] == task)['dependencies'] = dependencies

    def test_cycle_is_rejected_even_if_manifest_and_map_agree(self):
        self.set_dependency('AF-CLD-001', ['AF-CLD-003'])
        with self.assertRaisesRegex(validator.MapError, 'dependency cycle'): self.check()

    def test_godot_cannot_wait_for_unity_even_without_a_cycle(self):
        # Move Unity fixture dependencies earlier to avoid an incidental cycle.
        self.set_dependency('AF-CLD-053', ['AF-CLD-001'])
        self.set_dependency('AF-CLD-010', ['AF-CLD-053'])
        with self.assertRaisesRegex(validator.MapError, 'First Godot gate'): self.check()

    def test_unknown_pack_version_cannot_be_advertised(self):
        self.data['baseline']['pack_versions']['Godot'] = '4.x'
        with self.assertRaisesRegex(validator.MapError, 'Unaccepted pack version'): self.check()

    def test_actual_git_evidence_resolution_rejects_missing_object(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(validator.MapError, 'Pinned Core object check failed'):
                validator.validate(self.data, self.cloud, Path(directory))

    def test_pinned_source_check_is_read_only_and_checks_blob_types(self):
        upstream = {'items': [{'stable_id': row['id'], 'kind': 'task', 'title': row['title'],
                               'dependencies': row['dependencies']} for row in self.data['upstream_tasks']]}
        calls = []
        def git_read(repo, *args):
            calls.append(args)
            if args[0] == 'show': return json.dumps(self.cloud if args[1].endswith('agentfactory-cloud-backlog.json') else upstream)
            if args[0] == 'cat-file': return 'tree\n'
            return ''
        with patch.object(validator, 'git_read', side_effect=git_read):
            with self.assertRaisesRegex(validator.MapError, 'existing file'):
                validator.validate(self.data, self.cloud, Path('.'))
        self.assertTrue(all(c[0] in {'show', 'merge-base', 'cat-file'} for c in calls))


if __name__ == '__main__':
    unittest.main()
