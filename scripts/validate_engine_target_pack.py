"""AF-CLD-005 consumer contract rehearsal; never executes an engine or grants access."""
from copy import deepcopy
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def load():
    return tuple(json.loads((ROOT / 'contracts/v1' / name).read_text(encoding='utf-8'))
                 for name in ('engine-target-pack.json', 'engine-target-pack-fixtures.json'))


def typed(value, kind):
    if kind == 'sha256':
        return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None
    if kind == 'version':
        return isinstance(value, str) and re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value) is not None
    if kind == 'boolean':
        return type(value) is bool
    if kind in ('positive_integer', 'nonnegative_integer'):
        return type(value) is int and value >= (1 if kind == 'positive_integer' else 0)
    if kind == 'string_list':
        return isinstance(value, list) and all(typed(v, 'string') for v in value) and len(value) == len(set(value))
    return isinstance(value, str) and bool(value.strip())


def validate_manifest(manifest, contract):
    if not isinstance(manifest, dict) or set(manifest) != set(contract['manifest_fields']):
        raise ValueError('Exact manifest fields required')
    if manifest['contract_version'] != contract['contract_version']:
        raise ValueError('Unsupported contract version')
    for key, value in manifest.items():
        kind = 'sha256' if key.endswith('sha256') else 'version' if key.endswith('version') else 'string_list' if key == 'operations' else 'string'
        if not typed(value, kind):
            raise ValueError('Invalid manifest field: ' + key)
    if not manifest['operations'] or not set(manifest['operations']) <= set(contract['operations']):
        raise ValueError('Unknown or empty operation set')
    if manifest['target_id'] not in contract['targets']:
        raise ValueError('Unknown target')


def validate_request(request, contract):
    if set(request) != {'contract_version', 'mode', 'binding', 'limits', 'permissions', 'cancelled', 'gates'}:
        raise ValueError('Exact request fields required')
    if request['contract_version'] != contract['contract_version'] or request['mode'] not in {'live', 'simulation'}:
        raise ValueError('Unsupported request version or mode')
    binding = request['binding']
    if set(binding) != set(contract['request_binding']):
        raise ValueError('Complete immutable binding required')
    for key, value in binding.items():
        if key in {'build_id', 'artifact_sha256'} and value is None:
            continue
        kind = 'sha256' if key.endswith('sha256') else 'positive_integer' if key == 'run_attempt' else 'version' if key.endswith('version') else 'string'
        if not typed(value, kind):
            raise ValueError('Invalid request binding: ' + key)
    if (binding['build_id'] is None) != (binding['artifact_sha256'] is None):
        raise ValueError('Build identity must be complete or absent')
    if binding['operation'] in {'run', 'collect_crash'} and binding['artifact_sha256'] is None:
        raise ValueError('Exact built artifact required for runtime operations')
    if set(request['limits']) != set(contract['request_limits']):
        raise ValueError('Explicit execution limits required')
    for key, value in request['limits'].items():
        if not typed(value, 'nonnegative_integer' if key == 'budget_minor' else 'positive_integer'):
            raise ValueError('Invalid execution limit')
    if not typed(request['permissions'], 'string_list') or not typed(request['gates'], 'string_list') or not typed(request['cancelled'], 'boolean'):
        raise ValueError('Invalid authority/cancellation input')


def plan(request, manifest, engine, contract):
    """Synthetic compatibility decision only; no subprocess, filesystem or network action."""
    validate_manifest(manifest, contract)
    validate_request(request, contract)
    binding = request['binding']
    def blocked(reason, action):
        return {'status': 'blocked', 'reason': reason, 'next_action': action, 'dispatch': None}
    if request['cancelled']:
        return {'status': 'cancelled', 'reason': 'operator_cancelled', 'next_action': 'Review before a new attempt', 'dispatch': None}
    operation = binding['operation']
    if operation not in contract['operations'] or operation not in manifest['operations'] or operation not in engine.get('operations', []):
        return blocked('unsupported_operation', 'Choose an implemented operation')
    expected = {'engine_id':engine.get('id'), 'engine_version':engine.get('version'), 'engine_sha256':engine.get('sha256'),
                'pack_id':manifest['id'], 'pack_version':manifest['version'], 'pack_sha256':manifest['sha256'],
                'target_id':manifest['target_id'], 'target_version':manifest['target_version']}
    if any(binding[k] != v for k,v in expected.items()) or manifest['engine_id'] != engine.get('id') or manifest['engine_version'] != engine.get('version'):
        return blocked('incompatible_identity', 'Select matching immutable engine, pack and target versions')
    target = binding['target_id']
    if target not in contract['targets'] or target not in engine.get('targets', []):
        return blocked('unsupported_target', 'Choose a supported target')
    if not set(contract['targets'][target]) <= set(request['gates']):
        return blocked('target_gate_required', 'Obtain the target-specific toolchain and authority decisions')
    if contract['permission_by_operation'][operation] not in request['permissions']:
        return blocked('permission_required', 'Request the exact operation permission')
    # A fixture flag, caller-supplied gate or manifest can never grant live qualification.
    if request['mode'] != 'simulation':
        return blocked('live_qualification_unavailable', 'Integrate Core authenticated qualification and action-time authorization')
    return {'status':'compatible_simulation', 'reason':None, 'next_action':'Run the synthetic conformance fixture',
            'dispatch':{'operation':operation, 'adapter_id':engine['id']}}


def validate_result(result, request, contract):
    validate_request(request, contract)
    if set(result) != set(contract['result_fields']):
        raise ValueError('Exact result envelope required')
    if result['contract_version'] != contract['contract_version'] or result['binding'] != request['binding'] or result['mode'] != request['mode']:
        raise ValueError('Result version, attempt or mode mismatch')
    validate_request({**request, 'binding': result['binding']}, contract)
    if result['status'] not in contract['result_statuses']:
        raise ValueError('Unknown result status')
    if not typed(result['evidence_ref'], 'string'):
        raise ValueError('Evidence reference required')
    if result['status'] != 'succeeded':
        if result['payload'] is not None or not typed(result['reason'], 'string') or not typed(result['next_action'], 'string'):
            raise ValueError('Non-success needs a reason and next action, never a success payload')
        return
    if request['cancelled']:
        raise ValueError('Cancelled request cannot succeed')
    fields = contract['operations'].get(request['binding']['operation'])
    if fields is None or not isinstance(result['payload'], dict) or set(result['payload']) != set(fields):
        raise ValueError('Typed operation payload required')
    if result['reason'] is not None or result['next_action'] is not None:
        raise ValueError('Success cannot carry failure semantics')
    if not all(typed(result['payload'][key],kind) for key,kind in fields.items()):
        raise ValueError('Invalid operation result type')
    payload = result['payload']
    if request['binding']['operation'] == 'run' and payload['artifact_sha256'] != request['binding']['artifact_sha256']:
        raise ValueError('Runtime artifact differs from the requested build')
    if (('errors' in payload and payload['errors'] != 0) or ('failed' in payload and payload['failed'] != 0)
            or ('workspace_ready' in payload and not payload['workspace_ready']) or ('redacted' in payload and not payload['redacted'])):
        raise ValueError('Failed checks cannot be reported as success')


def run_fixtures(contract, fixtures):
    if fixtures['contract_version'] != contract['contract_version'] or fixtures['synthetic'] is not True:
        raise ValueError('Versioned synthetic fixtures required')
    count = 0
    for engine in fixtures['engines']:
        manifest = deepcopy(fixtures['manifest']); request = deepcopy(fixtures['request'])
        manifest.update(engine_id=engine['id'], engine_version=engine['version'])
        request['binding'].update(engine_id=engine['id'], engine_version=engine['version'], engine_sha256=engine['sha256'])
        for operation in contract['operations']:
            request['binding']['operation'] = operation
            if plan(request, manifest, engine, contract)['status'] != 'compatible_simulation':
                raise ValueError('Fixture dispatch rejected')
            result = {'contract_version':contract['contract_version'], 'binding':deepcopy(request['binding']), 'status':'succeeded',
                      'mode':'simulation', 'payload':fixtures['payloads'][operation], 'reason':None, 'next_action':None, 'evidence_ref':'synthetic:result'}
            validate_result(result, request, contract); count += 1
    return count


if __name__ == '__main__':
    contract, fixtures = load()
    print(f'Validated {run_fixtures(contract, fixtures)} synthetic operation results; no engine ran and no live target is qualified.')
