"""Real durable intake and conflict tests; AI responses here are explicitly synthetic."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from agentfactory_cloud.game_briefs import BriefConflict, BriefStore, FIELDS, LocalBriefModel, selected_proposal, source_segments, sha, validate_extraction, validate_proposal
from agent_factory.mission_intake import AutonomousMissionIntakeService
from agent_factory.storage import SQLiteStorage


def sample():
    return {'fields': {key: 'Synthetic ' + key for key in FIELDS},
            'assumptions': ['A single small level is an unconfirmed suggestion.'],
            'questions': [{'field': 'controls', 'question': 'Which controls?', 'options': ['Keyboard', 'Touch']}]}


class FakeModel:
    model = 'synthetic-test-model'
    profile_sha256 = 'a' * 64
    calls = 0

    def propose(self, brief, actor):
        self.calls += 1
        return sample(), {'scope': 'synthetic-test', 'input_revision': brief['revision']}


class GameBriefTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = BriefStore(Path(self.temporary.name))

    def create(self, original='A small game about collecting seeds', command='create-0001'):
        return self.store.create(original, 'Local Creator', command)

    def test_exact_ukrainian_english_original_survives_core_and_store_reopen(self):
        for index, original in enumerate(('  Хочу гру: збирати насіння!\r\nБез боїв.  ', '  A garden game.\nKeep the birds safe!  ')):
            brief = self.create(original, f'create-000{index}')
            loaded = BriefStore(Path(self.temporary.name)).get(brief['id'], 'Local Creator')
            self.assertEqual(loaded['original_text'], original)
            self.assertEqual(loaded['source_sha256'], sha(original))
            with closing(SQLiteStorage(self.store.core_database)) as core:
                content = AutonomousMissionIntakeService(core).get_source(brief['core_source_id']).content
                self.assertEqual(content, original)

    def test_create_replay_is_idempotent_but_changed_input_conflicts(self):
        first = self.create(); self.assertEqual(self.create()['id'], first['id'])
        with self.assertRaises(BriefConflict): self.create('Different idea')
        self.assertEqual(len(self.store.list('Local Creator')), 1)

    def test_interruption_after_core_commit_recovers_without_duplicate_intake(self):
        real_close = SQLiteStorage.close
        def interrupt(core):
            real_close(core)
            raise OSError('Synthetic stop after Core commit')
        with patch.object(SQLiteStorage, 'close', interrupt):
            with self.assertRaises(OSError): self.create()
        brief = self.create()
        with closing(sqlite3.connect(self.store.core_database)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM autonomous_missions').fetchone()[0], 1)
        self.assertEqual(brief['revision'], 1)

    def test_other_local_actor_cannot_read_or_edit_a_brief(self):
        brief = self.create()
        self.assertEqual(self.store.list('Other'), [])
        with self.assertRaises(KeyError): self.store.get(brief['id'], 'Other')
        with self.assertRaises(KeyError): self.store.save(brief['id'], 'Other', 1, 'edit-0001', sample())

    def test_edits_keep_original_and_persist_immutable_versions(self):
        brief = self.create(); proposed = sample()
        updated = self.store.save(brief['id'], 'Local Creator', 1, 'edit-0001', proposed)
        self.assertEqual(updated['revision'], 2)
        self.assertEqual(updated['original_text'], brief['original_text'])
        self.assertNotEqual(updated['content_sha256'], brief['content_sha256'])
        self.assertEqual(self.store.get(brief['id'], 'Local Creator', revision=1)['fields']['genre'], '')
        with closing(self.store.connect()) as db:
            with self.assertRaises(sqlite3.IntegrityError): db.execute("UPDATE briefs SET original='changed'")
            with self.assertRaises(sqlite3.IntegrityError): db.execute("UPDATE revisions SET document='{}'")

    def test_concurrent_edits_save_one_version_and_do_not_overwrite(self):
        brief = self.create()
        def edit(index):
            try:
                return self.store.save(brief['id'], 'Local Creator', 1, f'edit-000{index}', sample())['revision']
            except BriefConflict:
                return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(edit, (1, 2))), [2, 'conflict'])

    def test_answer_history_is_bound_to_the_visible_question_and_version(self):
        brief = self.create()
        suggested = self.store.save(brief['id'], 'Local Creator', 1, 'edit-0001', sample())
        proposal = sample(); proposal['fields']['controls'] = 'Touch'; proposal['questions'] = []
        answered = self.store.save(brief['id'], 'Local Creator', 2, 'edit-0002', proposal, answers={'controls': 'Touch'})
        self.assertEqual(answered['clarification_history'][0]['question'], suggested['questions'][0]['question'])
        self.assertEqual(answered['clarification_history'][0]['answered_at_revision'], 3)
        with self.assertRaises(ValueError):
            self.store.save(brief['id'], 'Local Creator', 3, 'edit-0003', proposal, answers={'genre': 'Unknown question'})

    def test_ai_attempt_replay_does_not_repeat_inference(self):
        brief = self.create(); model = FakeModel()
        proposed = self.store.suggest(brief['id'], 'Local Creator', 1, 'suggest-0001', model)
        replay = self.store.suggest(brief['id'], 'Local Creator', 1, 'suggest-0001', model)
        self.assertEqual(model.calls, 1); self.assertEqual(replay['revision'], proposed['revision'])
        self.assertEqual(proposed['analysis_kind'], 'ai_proposal')
        self.assertEqual(proposed['original_text'], brief['original_text'])
        with self.assertRaises(BriefConflict): self.store.suggest(brief['id'], 'Local Creator', 2, 'suggest-0001', model)

    def test_failed_ai_keeps_original_and_same_attempt_never_retries(self):
        brief = self.create()
        class Failed(FakeModel):
            def propose(self, brief, actor): self.calls += 1; raise ValueError('synthetic failure')
        model = Failed()
        with self.assertRaises(ValueError): self.store.suggest(brief['id'], 'Local Creator', 1, 'suggest-0001', model)
        with self.assertRaises(BriefConflict): self.store.suggest(brief['id'], 'Local Creator', 1, 'suggest-0001', model)
        self.assertEqual(model.calls, 1)
        self.assertEqual(self.store.get(brief['id'], 'Local Creator')['revision'], 1)

    def test_interrupted_attempt_remains_fenced_after_store_reopen(self):
        brief = self.create()
        class Interrupted(FakeModel):
            def propose(self, brief, actor): self.calls += 1; raise KeyboardInterrupt()
        model = Interrupted()
        with self.assertRaises(KeyboardInterrupt): self.store.suggest(brief['id'], 'Local Creator', 1, 'suggest-0001', model)
        reopened = BriefStore(Path(self.temporary.name))
        with self.assertRaises(BriefConflict): reopened.suggest(brief['id'], 'Local Creator', 1, 'suggest-0001', model)
        self.assertEqual(model.calls, 1)

    def test_local_route_rejects_ambient_remote_daemon_before_network(self):
        model = LocalBriefModel('qwen2.5-coder:7b')
        with patch.dict('os.environ', {'OLLAMA_HOST': 'https://remote.example'}), patch('agentfactory_cloud.game_briefs.build_opener') as network:
            with self.assertRaises(ValueError): model.installed_digest()
            network.assert_not_called()
        with self.assertRaises(ValueError): LocalBriefModel('unapproved-model')

    def test_extraction_cannot_change_quantities_or_invent_losing_rules(self):
        brief = self.create('Collect three stars with arrow keys on Windows. No combat.')
        proposal = {'fields': {key: '' for key in FIELDS}, 'assumptions': [], 'questions': []}
        proposal['fields']['first_playable'] = 'Collect one star'
        with self.assertRaises(ValueError): validate_extraction(proposal, brief)
        proposal['fields']['first_playable'] = 'Collect three stars'
        proposal['fields']['win_lose_rules'] = 'Lose when the timer ends'
        with self.assertRaises(ValueError): validate_extraction(proposal, brief)
        proposal['fields']['win_lose_rules'] = ''
        proposal['fields']['core_loop'] = 'Collect three stars'
        proposal['fields']['controls'] = 'arrow keys'
        proposal['fields']['target_platform'] = 'Windows'
        self.assertEqual(validate_extraction(proposal, brief)['questions'], [])

    def test_vague_extraction_has_three_plain_questions_with_suggested_answers(self):
        brief = self.create('I want a fun game.')
        proposal = {'fields': {key: '' for key in FIELDS}, 'assumptions': [], 'questions': []}
        result = validate_extraction(proposal, brief)
        self.assertEqual(len(result['questions']), 3)
        self.assertTrue(all(len(q['options']) in (2, 3) for q in result['questions']))
        self.assertFalse(result['fields']['target_platform'])

    def test_source_selection_cannot_invent_text_or_select_nonexistent_statements(self):
        brief = self.create('Зібрати три зірки. Грати на Windows. Без боїв.')
        segments = source_segments(brief['original_text'])
        selection = {key: 0 for key in FIELDS}; selection['core_loop'] = 1; selection['target_platform'] = 2
        result = selected_proposal(selection, segments, brief)
        self.assertEqual(result['fields']['core_loop'], 'Зібрати три зірки.')
        for invalid in [True, '1', 1.5, -1, len(segments) + 1]:
            with self.subTest(invalid=invalid):
                selection['core_loop'] = invalid
                with self.assertRaises(ValueError): selected_proposal(selection, segments, brief)

    def test_source_selection_keeps_lines_without_punctuation(self):
        original = 'Зібрати три зірки\r\nГрати на Windows\nБез боїв'
        self.assertEqual(source_segments(original), ['Зібрати три зірки', 'Грати на Windows', 'Без боїв'])

    def test_repeated_ai_suggestions_preserve_explicit_human_fields(self):
        brief = self.create(); chosen = sample(); chosen['fields'] = {key: '' for key in FIELDS}
        chosen['fields']['controls'] = 'Only the arrow keys'
        self.store.save(brief['id'], 'Local Creator', 1, 'human-0001', chosen)
        model = FakeModel()
        for revision in (2, 3):
            result = self.store.suggest(brief['id'], 'Local Creator', revision, f'suggest-000{revision}', model)
            self.assertEqual(result['fields']['controls'], 'Only the arrow keys')
            self.assertNotIn('controls', [q['field'] for q in result['questions']])
            self.assertIn('controls', result['human_fields'])

    def test_concurrent_human_edit_wins_over_stale_ai_response(self):
        brief = self.create(); store = self.store
        class Delayed(FakeModel):
            def propose(self, brief, actor):
                store.save(brief['id'], actor, 1, 'human-0001', sample())
                return super().propose(brief, actor)
        with self.assertRaises(BriefConflict): self.store.suggest(brief['id'], 'Local Creator', 1, 'suggest-0001', Delayed())
        self.assertEqual(self.store.get(brief['id'], 'Local Creator')['analysis_kind'], 'human_edited')

    def test_model_cannot_inject_unknown_fields_or_unbounded_questions(self):
        malformed = sample(); malformed['approved'] = True
        with self.assertRaises(ValueError): validate_proposal(malformed)
        malformed = sample(); malformed['questions'] *= 4
        with self.assertRaises(ValueError): validate_proposal(malformed)
        malformed = sample(); malformed['fields']['genre'] = 'a' * 1501
        with self.assertRaises(ValueError): validate_proposal(malformed)
        malformed = sample(); malformed['questions'][0]['options'] = ['same', 'same']
        with self.assertRaises(ValueError): validate_proposal(malformed)

    def test_no_default_model_calls_and_no_boolean_revision(self):
        brief = self.create()
        with self.assertRaises(ValueError): self.store.suggest(brief['id'], 'Local Creator', 1, 'suggest-0001', None)
        with self.assertRaises(ValueError): self.store.save(brief['id'], 'Local Creator', True, 'edit-0001', sample())

    def test_intake_creates_no_execution_approval(self):
        self.create()
        with closing(sqlite3.connect(self.store.core_database)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM autonomous_backlog_approvals').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT phase FROM autonomous_missions').fetchone()[0], 'DRAFT')


if __name__ == '__main__': unittest.main()
