"""Reviewable first-playable proposals; no inference or execution authority."""
from contextlib import closing
import json
import re

from .game_briefs import BriefConflict, command_key, encoded, now, sha, text

POLICY = 'small-2d-scope-v1'
LABELS = {
    'goal': 'One playable goal', 'controls': 'Controls', 'win_rule': 'How the player wins',
    'visual_style': 'Look and feel', 'assumptions': 'Assumptions to review',
    'exclusions': 'Outside this first version', 'deferred_roadmap': 'Your longer-term roadmap',
}
ENGINES = {'godot': 'Godot 2D / GDScript', 'unreal': 'Unreal Engine', 'unity': 'Unity', 'other': 'Another engine'}
TARGETS = {'windows': 'Windows', 'web': 'Web browser'}
LARGE = re.compile(r'\b(?:AAA|MMORPG|multiplayer|open[ -]world|VR)\b|відкрит\w*\s+світ|мультиплеєр|багатокористува', re.I)


def validate_scope(value):
    if not isinstance(value, dict) or set(value) != {*LABELS, 'engine', 'target', 'token_allowance'}:
        raise ValueError('Use the supported scope fields.')
    for key in LABELS:
        text(value[key], 1500, empty=True)
    if (not isinstance(value['engine'], str) or not isinstance(value['target'], str)
            or value['engine'] not in ENGINES or value['target'] not in TARGETS):
        raise ValueError('Choose an engine and target from the list.')
    if type(value['token_allowance']) is not int or not 1000 <= value['token_allowance'] <= 200000:
        raise ValueError('The planning allowance must be between 1,000 and 200,000 tokens.')


def proposal(brief):
    original = brief['original_text']
    large = bool(LARGE.search(original))
    engine = next((key for key in ('unreal', 'unity', 'godot') if re.search(r'\b' + key + r'\b', original, re.I)), 'godot')
    fields = brief['fields']
    later = []
    if engine != 'godot':
        later.append('Qualify ' + ENGINES[engine] + ' and port the accepted small slice before adding features.')
    if re.search(r'MMORPG|multiplayer|мультиплеєр|багатокористува', original, re.I):
        later.append('After single-player works, design and test a small multiplayer session with its own budget.')
    if re.search(r'open[ -]world|відкрит\w*\s+світ', original, re.I):
        later.append('After one room works, test a second area and world streaming before expanding the world.')
    if re.search(r'\bAAA\b', original, re.I):
        later.append('After gameplay is proven, measure the art/performance budget and qualify licensed assets.')
    if re.search(r'agentic|AI.?NPC|NPC.?AI|LLM', original, re.I):
        later.append('Qualify one NPC with bounded actions, saved memory and model-outage recovery before expanding AI world systems.')
    # These are labelled template suggestions, not extracted source requirements.
    return {
        'engine': engine, 'target': 'web' if re.search(r'\bweb\b|браузер', fields['target_platform'], re.I) else 'windows',
        'goal': ('Collect three markers and reach an exit in one small room.' if large else
                 fields['first_playable'] or fields['core_loop'] or 'Collect three markers and reach an exit in one small room.'),
        'controls': fields['controls'] or 'Use the arrow keys to move.',
        'win_rule': fields['win_lose_rules'] if fields['win_lose_rules'] and not large else 'Show success only after the playable goal above is completed.',
        'visual_style': fields['visual_style'] or 'Simple placeholder shapes with clear contrast.',
        'assumptions': 'Suggested first milestone: one player, one small 2D level and one goal. Review the proposed controls and win condition. Placeholder art uses owned or licensed assets.',
        'exclusions': 'Online multiplayer, an open world, AAA visuals, new runtime AI systems, paid assets and public publishing are outside this first milestone.',
        'deferred_roadmap': fields['deferred_scope'] or '\n'.join(later) or 'After the first playable, review the remaining original requirements and plan one tested addition at a time.',
        'token_allowance': 40000,
    }


def evaluate(scope):
    validate_scope(scope)
    limitations = []
    if scope['engine'] != 'godot':
        limitations.append('This milestone has only a Godot 2D planning template. Choose Godot explicitly for a separate small slice, or keep this draft for later engine qualification.')
    if LARGE.search(' '.join(scope[key] for key in ('goal', 'controls', 'win_rule'))):
        limitations.append('The playable goal still mentions a feature outside this small 2D template. Move that feature to the roadmap and choose one local player goal.')
    for key in ('goal', 'controls', 'win_rule', 'assumptions', 'exclusions'):
        if not scope[key].strip():
            limitations.append('Fill in ' + LABELS[key].lower() + ' before agreeing to this scope.')
    goal, controls, win = scope['goal'], scope['controls'], scope['win_rule']
    tasks = [
        ('project', 'Create the small project', [],
         ['A source project opens with one 2D level.', 'The project contains only the chosen first-milestone scope.']),
        ('controls', 'Implement player control', ['project'],
         ['The player can use these controls: ' + controls, 'Movement stays inside the playable room.']),
        ('goal', 'Implement the goal and win condition', ['controls'],
         ['The player can complete this goal: ' + goal, 'Success follows this rule: ' + win, 'A fresh attempt resets objective progress.']),
        ('level', 'Make the level readable', ['goal'],
         ['The level uses this visual direction: ' + scope['visual_style'], 'The goal, exit and obstacles are visible.', 'Included assets have recorded reuse rights.']),
        ('playtest', 'Verify the playable loop', ['level'],
         ['An input-driven playtest completes the stated goal.', 'An incomplete attempt does not trigger success.', 'The game can restart and finish a second attempt; errors and results are recorded.']),
        ('package', 'Package and check the chosen target', ['playtest'],
         ['The exact ' + TARGETS[scope['target']] + ' build starts outside the editor.', 'The packaged build completes the same goal and control checks.', 'Record build hashes, logs and source export; no publish action is included.']),
    ]
    # Explicit synthetic planning assumptions; no observed usage or vendor quote.
    budget = {'basis': 'synthetic-small-slice-usage-v1', 'route': 'local-model-assumption',
              'tasks': len(tasks), 'input_tokens_per_attempt': 2000, 'output_tokens_per_attempt': 600,
              'attempts_min': 1, 'attempts_max': 2, 'estimated_tokens_min': 15600,
              'estimated_tokens_max': 31200, 'token_allowance': scope['token_allowance'],
              'estimated_paid_api_fee': '0.00', 'currency': 'CHF',
              'excludes': ['hardware', 'electricity', 'hosting', 'assets', 'human review'],
              'pricing_quote': False, 'usage_measured': False, 'execution_budget_grant': False}
    if scope['token_allowance'] < budget['estimated_tokens_max']:
        limitations.append('The chosen allowance is below the template estimate. Revise the plan or allowance before agreeing; this estimate is not a guarantee.')
    return {
        'leaf_tasks': [{'id': ident, 'title': title, 'depends_on': deps, 'acceptance': checks}
                       for ident, title, deps, checks in tasks],
        'budget': budget, 'limitations': limitations, 'scope_agreement_available': not limitations,
        'template_limits': {'dimensions': 2, 'players': 1, 'levels': 1, 'online_multiplayer': False,
                            'new_agentic_runtime': False, 'public_publish': False},
        'execution_ready': False,
        'execution_next_action': 'Qualify the chosen engine, worker and model route, obtain independent review and separate execution/budget authority.',
        'alternative': {'engine': 'godot', 'target': scope['target'], 'description': 'A separate one-player 2D room with one goal; the original vision stays unchanged.'},
    }


class ScopePlans:
    def __init__(self, briefs):
        self.briefs = briefs
        with closing(briefs.connect()) as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS scope_plans (
                    id TEXT PRIMARY KEY, brief_id TEXT NOT NULL, actor TEXT NOT NULL, revision INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS scope_versions (
                    plan_id TEXT NOT NULL, revision INTEGER NOT NULL, document TEXT NOT NULL,
                    PRIMARY KEY(plan_id,revision));
                CREATE TABLE IF NOT EXISTS scope_commands (
                    actor TEXT NOT NULL, command_id TEXT NOT NULL, digest TEXT NOT NULL, plan_id TEXT NOT NULL,
                    PRIMARY KEY(actor,command_id));
                CREATE TRIGGER IF NOT EXISTS scope_version_immutable BEFORE UPDATE ON scope_versions
                BEGIN SELECT RAISE(ABORT,'scope versions are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS scope_version_durable BEFORE DELETE ON scope_versions
                BEGIN SELECT RAISE(ABORT,'scope versions are durable'); END;
                CREATE TRIGGER IF NOT EXISTS scope_owner_immutable BEFORE UPDATE OF id,brief_id,actor ON scope_plans
                BEGIN SELECT RAISE(ABORT,'scope ownership is immutable'); END;
            ''')

    def get(self, ident, actor, *, revision=None):
        with closing(self.briefs.connect()) as db:
            row = db.execute('SELECT * FROM scope_plans WHERE id=? AND actor=?', (ident, actor)).fetchone()
            if not row:
                raise KeyError('Scope plan unavailable.')
            brief = self.briefs.get(row['brief_id'], actor)
            saved = db.execute('SELECT document FROM scope_versions WHERE plan_id=? AND revision=?',
                               (ident, row['revision'] if revision is None else revision)).fetchone()
            if not saved:
                raise KeyError('Scope version unavailable.')
            document = json.loads(saved['document'])
            return {'id': ident, 'brief_id': row['brief_id'], **document,
                    'current_brief_revision': brief['revision'],
                    'stale': document['brief_revision'] != brief['revision']}

    def latest(self, brief_id, actor):
        self.briefs.get(brief_id, actor)
        with closing(self.briefs.connect()) as db:
            row = db.execute('SELECT id FROM scope_plans WHERE brief_id=? AND actor=? ORDER BY rowid DESC LIMIT 1',
                             (brief_id, actor)).fetchone()
        return self.get(row['id'], actor) if row else None

    def write(self, brief_id, actor, expected_brief, command, *, ident=None, expected_plan=None, scope=None, agree=False):
        command_key(command)
        if type(expected_brief) is not int or expected_brief < 1 or type(agree) is not bool:
            raise ValueError('A current brief version is required.')
        if ident is not None and (type(expected_plan) is not int or expected_plan < 1):
            raise ValueError('A current scope version is required.')
        request = sha(encoded([brief_id, expected_brief, ident, expected_plan, scope, agree]))
        with closing(self.briefs.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM scope_commands WHERE actor=? AND command_id=?', (actor, command)).fetchone()
            if old:
                if old['digest'] != request:
                    raise BriefConflict('That request identity belongs to a different scope action.')
                return self.get(old['plan_id'], actor)
            brief = self.briefs.get(brief_id, actor)
            if brief['revision'] != expected_brief:
                raise BriefConflict('The brief changed. Your scope edit is kept on screen; start a new draft from the current brief.')
            if ident is None:
                if agree or scope is not None:
                    raise ValueError('Create a reviewable draft before editing or agreeing.')
                existing = db.execute('SELECT id,revision FROM scope_plans WHERE brief_id=? AND actor=? ORDER BY rowid DESC LIMIT 1',
                                      (brief_id, actor)).fetchone()
                ident = existing['id'] if existing else sha(encoded([actor, command, 'scope']))[:32]
                revision = existing['revision'] + 1 if existing else 1
                scope = proposal(brief)
                if not existing:
                    db.execute('INSERT INTO scope_plans VALUES(?,?,?,?)', (ident, brief_id, actor, revision))
            else:
                previous = self.get(ident, actor)
                if previous['brief_id'] != brief_id:
                    raise KeyError('Scope plan unavailable.')
                if previous['revision'] != expected_plan or previous['brief_revision'] != expected_brief:
                    raise BriefConflict('A newer scope or brief exists. Your edit is kept on screen; reload before saving.')
                revision = expected_plan + 1
                if agree:
                    if scope is not None:
                        raise ValueError('Save edits before agreeing to the displayed version.')
                    scope = previous['scope']
            evaluation = evaluate(scope)
            if agree and not evaluation['scope_agreement_available']:
                raise ValueError(evaluation['limitations'][0])
            document = {'revision': revision, 'brief_revision': brief['revision'],
                        'brief_sha256': brief['content_sha256'], 'source_sha256': brief['source_sha256'],
                        'policy_version': POLICY, 'created_at': now(), 'state': 'scope_agreed' if agree else 'draft',
                        'scope': scope, **evaluation,
                        'agreement': {'actor': actor, 'reviewed_plan_revision': expected_plan,
                                      'execution_authority': False} if agree else None}
            document['content_sha256'] = sha(encoded(document))
            db.execute('INSERT INTO scope_versions VALUES(?,?,?)', (ident, revision, encoded(document)))
            db.execute('UPDATE scope_plans SET revision=? WHERE id=?', (revision, ident))
            db.execute('INSERT INTO scope_commands VALUES(?,?,?,?)', (actor, command, request, ident))
        return self.get(ident, actor)
