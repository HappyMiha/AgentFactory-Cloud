"""Synthetic reference evaluator for AF-CLD-006; no real evidence verification."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timezone required')
    return result


def load():
    folder = ROOT / 'contracts/v1'
    return tuple(json.loads((folder / name).read_text(encoding='utf-8'))
                 for name in ('evidence-policy.json', 'evidence-scenarios.json'))


def immutable_version(value):
    """Structural pinning only; trusted producers verify actual immutable releases."""
    if not isinstance(value, str) or len(value) > 128:
        return False
    if re.fullmatch(r'sha256:[0-9a-f]{64}', value):
        return True
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+){2}(?:[a-z][0-9]+)?(?:[-+.][A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?', value):
        return False
    floating = {'latest', 'main', 'master', 'head', 'nightly', 'current', 'default', 'tip', 'next', 'x'}
    return not floating.intersection(re.split(r'[-+.]', value.lower()))


def validate_subject(subject, policy):
    if not isinstance(subject, dict) or set(subject) != set(policy['binding_fields']):
        raise ValueError('Exact complete subject binding required')
    for key, value in subject.items():
        if value is None and key in ('build_id', 'artifact_sha256'):
            valid = True
        elif key == 'run_attempt':
            valid = type(value) is int and value > 0
        elif key.endswith('_sha256'):
            valid = isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)
        elif key in policy['immutable_version_fields']:
            valid = immutable_version(value)
        else:
            valid = isinstance(value, str) and bool(value.strip())
        if not valid:
            raise ValueError(f'Invalid subject field: {key}')


def binding_for(subject, kind):
    # Readiness can be checked before an artifact exists; later gates need it.
    excluded = {'build_id', 'artifact_sha256'} if kind == 'environment' else set()
    return {key: value for key, value in subject.items() if key not in excluded}


def valid_context(context, fields):
    if not isinstance(context, dict) or set(context) != set(fields):
        return False
    for field, value in context.items():
        if field.endswith('_revision') or field == 'price_minor':
            valid = type(value) is int and value >= (1 if field.endswith('_revision') else 0)
        else:
            valid = isinstance(value, str) and bool(value.strip())
        if not valid:
            return False
    return 'currency' not in context or bool(re.fullmatch('[A-Z]{3}', context['currency']))


def problem(record, kind, bundle, policy, now):
    spec = policy['checks'][kind]
    if record.get('status') != 'passed':
        return 'not_passed'
    if record.get('mode') != 'live':
        return 'simulation'
    if record.get('level') != spec['level']:
        return 'wrong_level'
    if (kind != 'environment' and (bundle['subject']['build_id'] is None or bundle['subject']['artifact_sha256'] is None)
            or record.get('binding') != binding_for(bundle['subject'], kind)):
        return 'wrong_binding'
    try:
        if not timestamp(record['checked_at']) <= now < timestamp(record['expires_at']):
            return 'stale'
    except (KeyError, ValueError, TypeError, AttributeError):
        return 'stale'
    issuer = bundle['trusted_issuers'].get(record.get('issuer_id'))
    if (not issuer or issuer.get('active') is not True
            or issuer.get('tenant_id') != bundle['subject']['tenant_id']
            or spec['issuer_role'] not in issuer.get('roles', [])
            or not isinstance(record.get('evidence_ref'), str) or not record['evidence_ref'].strip()):
        return 'untrusted_issuer'
    if spec.get('use') and record.get('use') != spec['use']:
        return 'wrong_use'
    if spec.get('independent'):
        mode = issuer.get('review_mode')
        model = issuer.get('model_identity')
        if mode == 'human_only':
            if issuer.get('kind') != 'human' or model is not None:
                return 'review_identity_missing'
        elif mode == 'ai_assisted':
            if (issuer.get('kind') not in ('human', 'service') or not isinstance(model, str)
                    or not re.fullmatch(r'[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}', model)):
                return 'review_identity_missing'
        else:
            return 'review_identity_missing'
        if (record['issuer_id'] in bundle['producer_issuer_ids']
                or model in bundle['producer_model_identities']):
            return 'review_conflict'
    if spec.get('human'):
        if issuer.get('kind') != 'human':
            return 'human_required'
        if record['issuer_id'] != bundle.get('authorized_owner_id'):
            return 'untrusted_issuer'
    if kind in ('moderation', 'publish_rights', 'reviewer_approval', 'owner_acceptance'):
        if (not valid_context(bundle.get('release_context'), policy['review_fields'])
                or record.get('decision_context') != bundle['release_context']):
            return 'wrong_decision_context'
    if kind in ('sell_rights', 'seller_eligibility', 'sale_terms'):
        if (not valid_context(bundle.get('release_context'), policy['review_fields'])
                or not valid_context(bundle.get('sale_context'), policy['sale_fields'])
                or bundle['sale_context']['price_minor'] <= 0
                or record.get('decision_context') != {**bundle['release_context'], **bundle['sale_context']}):
            return 'wrong_decision_context'
    return None


def evaluate(bundle, policy, now):
    """Trusted fixture context is injected; never expose this as a public endpoint."""
    validate_subject(bundle['subject'], policy)
    now = timestamp(now)
    results = {}
    visiting = set()

    def gate(name):
        if name in visiting:
            raise ValueError('Gate dependency cycle')
        if name in results:
            return results[name]
        visiting.add(name)
        definition = policy['gates'][name]
        denied = []
        for dependency in definition['depends_on']:
            denied.extend(gate(dependency)['blockers'])
        for kind in definition['checks']:
            records = [r for r in bundle['evidence'] if r.get('check') == kind]
            reason = 'missing' if not records else 'duplicate' if len(records) > 1 else problem(records[0], kind, bundle, policy, now)
            if reason:
                denied.append({'check': kind, 'reason': reason, 'next_action': policy['failure_actions'][reason]})
        visiting.remove(name)
        results[name] = {'allowed': not denied, 'blockers': denied,
                         'label': definition['positive_copy'] if not denied else f'{name}: checks needed',
                         'next_action': definition['action'] if not denied else denied[0]['next_action']}
        return results[name]

    for name in policy['gates']:
        gate(name)
    return {'policy_version': policy['policy_version'], 'subject': deepcopy(bundle['subject']),
            'evaluated_at': now.isoformat(), 'gates': results,
            'verification': 'synthetic-reference-only; no real checks executed'}


def run_scenarios(policy, fixtures):
    for scenario in fixtures['scenarios']:
        bundle = deepcopy(fixtures['bundle'])
        for patch in scenario.get('evidence_patches', []):
            record = next(r for r in bundle['evidence'] if r['check'] == patch['check'])
            record.update(patch)
        for key in scenario.get('remove_checks', []):
            bundle['evidence'] = [r for r in bundle['evidence'] if r['check'] != key]
        bundle['subject'].update(scenario.get('subject_patch', {}))
        result = evaluate(bundle, policy, fixtures['now'])
        actual = [name for name, gate in result['gates'].items() if gate['allowed']]
        if actual != scenario['allowed_gates']:
            raise ValueError(f'{scenario["name"]}: {actual!r} != {scenario["allowed_gates"]!r}')
    return len(fixtures['scenarios'])


def main():
    policy, fixtures = load()
    if policy['policy_version'] != fixtures['policy_version']:
        raise ValueError('Policy/fixture versions differ')
    count = run_scenarios(policy, fixtures)
    print(f'Validated {count} synthetic scenarios across {len(policy["gates"])} separate gates; no real build accepted.')


if __name__ == '__main__':
    main()
