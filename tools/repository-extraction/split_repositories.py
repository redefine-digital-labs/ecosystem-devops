#!/usr/bin/env python3
"""Prepare real local repositories and reversibly activate verified whole packages.

No commit, remote, signing or deployment. Mixed packages stay in their existing
authority until their public contracts have actually been separated.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from source_transition_guard import source_inputs

WHOLE_PACKAGES = {
    'soulidity_standard': 'soul-standard',
    'soulidity_community': 'soul-community',
    'soulidity_visual': 'soul-extensions',
    'soulidity_model': 'soul-extensions',
}
ALL_PACKAGES = [
    'soulidity_standard', 'soulidity_foundation', 'soulidity_model',
    'soulidity_visual', 'soulidity_content', 'soulidity_application',
    'soulidity_community', 'soulidity_native', 'soulidity_v1',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def inputs(package):
    return [package / 'Move.toml', *sorted((package / 'sources').glob('*.move')),
            *sorted((package / 'tests').glob('*.move'))]


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def prepare(args):
    state_path = args.workspace / 'workspace.json'
    if state_path.exists():
        raise SystemExit('Existing workspace: use verify; never overwrite its baseline.')
    plan = json.loads((args.design / 'docs/open-ecosystem/MODULE_DELIVERY_PLAN.json').read_text())
    args.workspace.mkdir(parents=True, exist_ok=True)
    rows = []
    for module in plan['modules']:
        repo = args.workspace / module['repository']
        if repo.exists() and any(repo.iterdir()):
            raise SystemExit(f'Refuse occupied repository path: {repo}')
        repo.mkdir(exist_ok=True)
        run(['git', 'init', '--initial-branch=codex/ecosystem-extraction', str(repo)])
        (repo / '.gitignore').write_text('**/build/\n.deps/\noutput/\n__pycache__/\n.DS_Store\n.env*\n*.key\n')
        rows.append({**module, 'local_path': str(repo), 'local_git_created': True,
                     'source_status': 'Not imported', 'remote_status': 'Not created',
                     'product_status': 'Not accepted', 'chain_cutover': False})
    prepared = []
    for name, repository in WHOLE_PACKAGES.items():
        src = args.source / 'move' / name
        target = args.workspace / repository / 'move' / name
        shutil.copytree(src, target, ignore=shutil.ignore_patterns('build', '.git'))
        original_hashes = {str(p.relative_to(src)): sha(p) for p in inputs(src)}
        if name == 'soulidity_model':
            manifest = target / 'Move.toml'
            text = manifest.read_text().replace('local = "../soulidity_standard"',
                'local = "../../../soul-standard/move/soulidity_standard"')
            text = text.replace('local = "../soulidity_foundation"',
                'local = "../../.deps/soulidity_foundation"')
            manifest.write_text(text)
            dependency = args.source / 'move/soulidity_foundation'
            snapshot = args.workspace / repository / '.deps/soulidity_foundation'
            shutil.copytree(dependency, snapshot, ignore=shutil.ignore_patterns('build', '.git'))
            put(args.workspace / repository / 'dependency-pins.json', {
                'kind': 'local-development-candidate', 'runtime_gate': False,
                'dependencies': [{'package': 'soulidity_foundation', 'authority': str(dependency),
                    'materialized_read_only': str(snapshot),
                    'files': {str(p.relative_to(dependency)): sha(p) for p in inputs(dependency)}}],
                'remote_revision': None,
                'remaining': 'Replace local source locator with an approved immutable release before remote CI.'})
        prepared.append({'package': name, 'repository': repository,
            'old_path': str(src), 'canonical_candidate': str(target),
            'baseline_inputs': original_hashes,
            'candidate_inputs': {str(p.relative_to(target)): sha(p) for p in inputs(target)},
            'state': 'prepared', 'build_evidence': None})
    sources = []
    for name in ALL_PACKAGES:
        for path in sorted((args.source / 'move' / name / 'sources').glob('*.move')):
            repository = WHOLE_PACKAGES.get(name)
            sources.append({'original': str(path), 'sha256': sha(path),
                'current_writer': str(path), 'prepared_repository': repository,
                'state': 'prepared' if repository else 'retained / mixed extraction pending'})
    if len(sources) != 52:
        raise SystemExit(f'Expected current 52 production sources, found {len(sources)}')
    put(state_path, {'schema': 1, 'source_root': str(args.source), 'design_root': str(args.design),
        'repositories': rows, 'packages': prepared, 'production_sources': sources,
        'remote_objects_created': 0, 'commits_created': 0, 'chain_cutovers': 0,
        'status': 'Local repository construction; full modularization not complete'})
    print(f'Created {len(rows)} independent local Git repositories; prepared {len(prepared)} whole packages.')


def verify(args):
    state = json.loads((args.workspace / 'workspace.json').read_text())
    expected, derived, errors = source_inputs(state)
    if errors:
        result = {'passed': False, 'errors': errors, 'source_integrity': 'failed',
                  'remote_objects_created': 0, 'chain_cutovers': 0}
        put(args.workspace / 'verification.json', result)
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(1)
    for row in state['repositories']:
        repo = Path(row['local_path'])
        if run(['git', '-C', str(repo), 'rev-parse', '--show-toplevel']) != str(repo):
            errors.append(f"Wrong Git root: {repo}")
    seen = set()
    for row in state['production_sources']:
        path = Path(row['current_writer'])
        if not path.is_file() or sha(path) != expected[str(path)]:
            errors.append(f'Missing/changed source: {path}')
        original = Path(row['original'])
        if not original.is_file() or original.resolve() != path.resolve():
            errors.append(f'Original source does not resolve to sole current writer: {original}')
        canonical = str(path.resolve())
        if canonical in seen:
            errors.append(f'Duplicate source authority: {canonical}')
        seen.add(canonical)
    for row in state['packages']:
        target = Path(row['canonical_candidate'])
        for rel in row['candidate_inputs']:
            if sha(target / rel) != expected[str(target / rel)]:
                errors.append(f'Candidate changed since preparation: {target / rel}')
        if row['state'] == 'active-source':
            old = Path(row['old_path'])
            if not old.is_symlink() or old.resolve() != target:
                errors.append(f'Old path is not a forwarding locator: {old}')
    # Common source_inputs validates locators, current bytes and independent
    # recovery copies for all entry points, including mapping/build consumers.
    client_sources = {str(Path(row['canonical']).resolve())
        for extraction in state.get('client_source_extractions', []) for row in extraction['modules']}
    result = {'passed': not errors, 'local_git_repositories': len(state['repositories']),
        'production_sources': len(seen), 'derived_production_sources': len(derived), 'errors': errors,
        'client_source_files': len(client_sources),
        'remote_objects_created': 0, 'chain_cutovers': 0,
        'not_proof_of': ['business decoupling', 'deployed CI', 'independent upgrade authority', 'full product acceptance']}
    put(args.workspace / 'verification.json', result)
    print(json.dumps(result, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


def activate(args):
    verify(args)
    state_path = args.workspace / 'workspace.json'
    state = json.loads(state_path.read_text())
    expected, _, errors = source_inputs(state)
    if errors:
        raise SystemExit('\n'.join(errors))
    for row in state['packages']:
        if args.package and row['package'] != args.package:
            continue
        if row['state'] == 'active-source':
            continue
        package = row['package']
        evidence = Path(row.get('build_evidence') or args.workspace / 'build-evidence' / package / 'evidence.json')
        if not evidence.is_file():
            raise SystemExit(f'No successful independent build evidence: {package}')
        check = json.loads(evidence.read_text())
        current_inputs = {rel: expected[str(Path(row['canonical_candidate']) / rel)]
                          for rel in row['candidate_inputs']}
        if (check.get('exit_code') != 0 or check.get('test_exit_code') != 0
                or check.get('verification_exit_code') != 0
                or check.get('input_errors_after_build') != [] or check.get('input_errors_after_test') != []
                or check.get('candidate_inputs') != current_inputs
                or check.get('package') != package or check.get('candidate_path') != row['canonical_candidate']):
            raise SystemExit(f'Invalid/stale build evidence: {package}')
        src, target = Path(row['old_path']), Path(row['canonical_candidate'])
        for rel, baseline_digest in row['baseline_inputs'].items():
            if sha(src / rel) != baseline_digest:
                raise SystemExit(f'Original changed; abort before move: {src / rel}')
        frozen = args.source / 'output/ecosystem-construction/repository-split-2026-10-10/frozen-before' / package
        if frozen.exists():
            raise SystemExit(f'Refuse overwrite of original baseline: {frozen}')
        frozen.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(frozen))
        src.symlink_to(target, target_is_directory=True)
        row.update(state='active-source', frozen_before=str(frozen), build_evidence=str(evidence))
        for source in state['production_sources']:
            old_path = Path(source['original'])
            if old_path.parent.parent == src:
                source.update(current_writer=str(target / old_path.relative_to(src)), state='active-source')
        for repository in state['repositories']:
            if repository['repository'] == row['repository']:
                repository['source_status'] = 'Actual source authority for verified whole packages; remaining scope pending'
        put(state_path, state)
    verify(args)
    print('Activated verified selected packages. Old paths forward to one source authority; chain routes are unchanged.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'verify', 'activate'])
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--design', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--package')
    args = parser.parse_args()
    args.source, args.design, args.workspace = args.source.resolve(), args.design.resolve(), args.workspace.resolve()
    globals()[args.action](args)


if __name__ == '__main__':
    main()
