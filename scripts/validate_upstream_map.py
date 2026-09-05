#!/usr/bin/env python3
"""Validate the AF-CLD-003 planning map; never certify product readiness.

Default checks are offline. --core-repo additionally reads pinned objects from
an existing local Core clone, without checking it out, fetching or writing it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OWNERS = {'Core', 'Core.Packs', 'Cloud.Platform', 'Cloud.Games',
          'Cloud.Community', 'Cloud.Marketplace'}
SHA = re.compile(r'[0-9a-f]{40}')
JOURNEYS = {
    'AF-GC-026': ('Godot', {'AF-CLD-020', 'AF-CLD-034'}),
    'AF-GC-031': ('local/hybrid', {'AF-CLD-063', 'AF-CLD-065'}),
    'AF-GC-034': ('Unity', {'AF-CLD-053', 'AF-CLD-060'}),
    'AF-GC-037': ('export/share', {'AF-CLD-016', 'AF-CLD-032', 'AF-CLD-039'}),
}


class MapError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise MapError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value, label):
    require(isinstance(value, list) and all(text(x) for x in value), f'{label}: expected string list')
    require(len(value) == len(set(value)), f'{label}: duplicate values')
    return set(value)


def index(rows, label, key='id'):
    require(isinstance(rows, list), f'{label}: expected list')
    result = {}
    for row in rows:
        require(isinstance(row, dict) and text(row.get(key)), f'{label}: invalid record')
        ident = row[key]
        require(ident not in result, f'{label}: duplicate {ident}')
        result[ident] = row
    return result


def acyclic(graph, label):
    visiting, done = set(), set()
    def visit(node):
        require(node not in visiting, f'{label}: dependency cycle at {node}')
        if node in done:
            return
        visiting.add(node)
        for dep in graph[node]:
            require(dep in graph, f'{label}: unknown dependency {dep}')
            visit(dep)
        visiting.remove(node)
        done.add(node)
    for node in graph:
        visit(node)


def git_read(repo, *args):
    result = subprocess.run(['git', *args], cwd=repo, capture_output=True,
                            text=True, encoding='utf-8', timeout=30, check=False)
    require(result.returncode == 0, 'Pinned Core object check failed: ' + ' '.join(args))
    return result.stdout


def validate(data, cloud_manifest, core_repo=None):
    require(isinstance(data, dict) and data.get('schema_version') == 1, 'Unsupported map schema')
    require(data.get('purpose') == 'planning-only', 'Map must remain planning-only')
    baseline = data.get('baseline')
    require(isinstance(baseline, dict), 'Missing baseline')
    for name, repository, manifest in [
        ('core', 'HappyMiha/AgentFactory', 'examples/game-creator-backlog.json'),
        ('cloud', 'HappyMiha/AgentFactory-Cloud', 'examples/agentfactory-cloud-backlog.json')]:
        source = baseline.get(name)
        require(isinstance(source, dict), f'Missing {name} baseline')
        require(source.get('repository') == repository and source.get('manifest') == manifest,
                f'Unexpected {name} baseline source')
        require(isinstance(source.get('commit'), str) and SHA.fullmatch(source['commit']),
                f'{name} baseline must pin a full commit')
    pin = baseline['core']['commit']
    require(baseline.get('interface_version') == 'unqualified-at-pin', 'Unaccepted interface version claim')
    require(baseline.get('pack_versions') == {'Godot': None, 'Unity': None, 'Unreal': None},
            'Unaccepted pack version claim')
    evidence = index(data.get('evidence_catalog'), 'evidence')
    for ident, item in evidence.items():
        require(item.get('repository') == 'core' and isinstance(item.get('commit'), str)
                and SHA.fullmatch(item['commit']), f'{ident}: evidence needs a pinned Core commit')
        require(text(item.get('limit')), f'{ident}: missing evidence limitations')
        if item.get('kind') == 'source-inventory':
            require(item['commit'] == pin, f'{ident}: source evidence version mismatch')
            paths = strings(item.get('paths'), f'{ident} paths')
            require(bool(paths), f'{ident}: no source paths')
            for path in paths:
                require(not path.startswith('/') and '\\' not in path and ':' not in path
                        and all(part not in {'', '.', '..'} for part in path.split('/')),
                        f'{ident}: unsafe source path')
        elif item.get('kind') == 'merged-engineering-review':
            require(isinstance(item.get('url'), str) and re.fullmatch(
                r'https://github\.com/HappyMiha/AgentFactory/pull/[1-9][0-9]*(?:#[a-z0-9-]+)?', item['url']),
                f'{ident}: invalid engineering evidence URL')
        else:
            raise MapError(f'{ident}: unsupported evidence type')
    upstream = index(data.get('upstream_tasks'), 'upstream tasks')
    capabilities = index(data.get('capabilities'), 'Cloud capabilities')
    require(set(upstream) == {f'AF-GC-{n:03d}' for n in range(1, 43)}, 'Expected all 42 upstream tasks')
    require(set(capabilities) == {f'AF-CLD-{n:03d}' for n in range(1, 68)}, 'Expected all 67 Cloud tasks')
    require(isinstance(cloud_manifest, dict) and isinstance(cloud_manifest.get('items'), list),
            'Invalid Cloud manifest')
    current = index([i for i in cloud_manifest['items'] if i.get('kind') != 'epic'], 'Cloud manifest', 'stable_id')
    require(set(current) == set(capabilities), 'Cloud manifest coverage mismatch')
    graphs = {'Cloud': {}, 'upstream': {}}
    for name, rows in [('Cloud', capabilities), ('upstream', upstream)]:
        for ident, item in rows.items():
            require(isinstance(item.get('implementation_owner'), str)
                    and item['implementation_owner'] in OWNERS, f'{ident}: one implementation owner required')
            ev = strings(item.get('evidence'), f'{ident} evidence')
            require(bool(ev) and ev <= evidence.keys(), f'{ident}: missing or unknown evidence')
            # This version has source inventory/engineering reviews, no accepted Cloud results.
            require(item.get('qualification') in {'partial', 'missing', 'blocked'},
                    f'{ident}: verified needs separately accepted integration evidence; absent in this map version')
            deps = strings(item.get('dependencies'), f'{ident} dependencies')
            require(deps <= rows.keys(), f'{ident}: foreign or unknown scheduling dependency')
            graphs[name][ident] = deps
            if name == 'Cloud':
                require(item.get('core_version') == pin, f'{ident}: Core version mismatch')
                require(item.get('consumer_owner') == 'Cloud', f'{ident}: invalid consumer owner')
                require(item.get('decision') in {'reuse', 'extend', 'migrate', 'build'}, f'{ident}: missing reuse decision')
                refs = strings(item.get('upstream_ids'), f'{ident} upstream IDs')
                require(refs <= upstream.keys(), f'{ident}: unknown upstream reference')
                check = item.get('integration_test')
                require(isinstance(check, dict) and check.get('status') == 'not-accepted'
                        and text(check.get('scenario')), f'{ident}: planned integration test required')
                require(text(item.get('gap')), f'{ident}: unresolved evidence gap required')
                source = current[ident]
                require(item.get('capability') == source.get('title'), f'{ident}: task title drift')
                require(deps == set(source.get('dependencies', [])), f'{ident}: dependencies mismatch')
                require('milestone:' + str(item.get('milestone', '')).lower() in source.get('labels', []),
                        f'{ident}: milestone mismatch')
            else:
                require(text(item.get('title')) and text(item.get('limit')), f'{ident}: incomplete upstream audit')
                require(item.get('engineering_status') in {'planned', 'merged'}, f'{ident}: invalid engineering state')
                if item['engineering_status'] == 'merged':
                    require(any(evidence[e]['kind'] == 'merged-engineering-review'
                                and ident in evidence[e].get('upstream_ids', []) for e in ev),
                            f'{ident}: merged claim lacks accepted engineering evidence')
                expected = {c for c, row in capabilities.items() if ident in row.get('upstream_ids', [])}
                require(strings(item.get('cloud_consumers'), f'{ident} consumers') == expected,
                        f'{ident}: reverse traceability mismatch')
    for name, graph in graphs.items():
        acyclic(graph, name)
    links = index(data.get('journey_links'), 'journey links', 'upstream_id')
    require(links.keys() == JOURNEYS.keys(), 'Four milestone-specific journey links required')
    for ident, (name, targets) in JOURNEYS.items():
        link = links[ident]
        require(link.get('journey') == name and strings(link.get('cloud_ids'), ident) == targets,
                f'{ident}: wrong journey mapping')
        require(link.get('relation') == 'acceptance-reference' and link.get('scheduling_dependency') is False,
                f'{ident}: journey evidence must not become a scheduling prerequisite')
        require(all(ident in capabilities[c]['upstream_ids'] for c in targets), f'{ident}: missing capability trace')
    ancestors = set()
    def collect(node):
        for dep in graphs['Cloud'][node]:
            if dep not in ancestors:
                ancestors.add(dep)
                collect(dep)
    collect('AF-CLD-020')
    require(not any(capabilities[c]['milestone'] > 'M1' for c in ancestors),
            'First Godot gate must not depend on later optional qualification')
    gaps = index(data.get('unresolved_integrations'), 'unresolved integrations')
    require(bool(gaps), 'Missing unresolved integration list')
    for ident, gap in gaps.items():
        require(isinstance(gap.get('owner'), str) and gap['owner'] in OWNERS and text(gap.get('resolution')),
                f'{ident}: gap needs one owner and resolution')
        require(bool(strings(gap.get('cloud_tasks'), ident)) and set(gap['cloud_tasks']) <= capabilities.keys(),
                f'{ident}: unknown gap task')
    if core_repo is not None:
        cloud_pin = baseline['cloud']
        pinned_cloud = json.loads(git_read(ROOT, 'show', cloud_pin['commit'] + ':' + cloud_pin['manifest']))
        require(pinned_cloud == cloud_manifest, 'Pinned Cloud manifest drift; review and update the baseline')
        pinned = json.loads(git_read(core_repo, 'show', pin + ':' + baseline['core']['manifest']))
        source = index([i for i in pinned['items'] if i['kind'] != 'epic'], 'pinned upstream manifest', 'stable_id')
        require(source.keys() == upstream.keys(), 'Pinned upstream coverage mismatch')
        for ident, row in upstream.items():
            require(row['title'] == source[ident]['title'] and set(row['dependencies']) == set(source[ident]['dependencies']),
                    f'{ident}: pinned upstream task drift')
        for item in evidence.values():
            git_read(core_repo, 'merge-base', '--is-ancestor', item['commit'], pin)
            for path in item.get('paths', []):
                require(git_read(core_repo, 'cat-file', '-t', item['commit'] + ':' + path).strip() == 'blob',
                        f'{item["id"]}: evidence must reference an existing file')
    return f'Planning map valid: {len(capabilities)} Cloud capabilities, {len(upstream)} upstream tasks; no product gate accepted.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map', type=Path, default=ROOT / 'docs/upstream-capability-map.json')
    parser.add_argument('--core-repo', type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.map.read_text(encoding='utf-8'))
        cloud = json.loads((ROOT / 'examples/agentfactory-cloud-backlog.json').read_text(encoding='utf-8'))
        print(validate(data, cloud, args.core_repo))
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f'Upstream map rejected: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
