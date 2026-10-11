#!/usr/bin/env python3
"""Verify reversible source transformations without rewriting extraction baselines.

The original 52 responsibility rows retain their original SHA. New source bodies
require an explicit frozen-before chain; added implementation files are separate
authority rows. This is input integrity, not business acceptance or deployment.
"""
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_inputs(state):
    expected = {str(Path(r['current_writer'])): r['sha256']
                for r in state['production_sources']}
    for package in state.get('packages', []):
        for relative, digest in package['candidate_inputs'].items():
            path = str(Path(package['canonical_candidate']) / relative)
            if path in expected and expected[path] != digest:
                raise ValueError('Conflicting baseline input: ' + path)
            expected[path] = digest
    errors, derived, ids = [], [], set()
    for reference in state.get('source_transitions', []):
        manifest_path = Path(reference['path'])
        if not manifest_path.is_file() or sha(manifest_path) != reference['sha256']:
            errors.append('Transition manifest changed/missing: ' + str(manifest_path))
            continue
        manifest = json.loads(manifest_path.read_text())
        if manifest.get('schema') != 1 or not manifest.get('id') or manifest['id'] in ids:
            errors.append('Invalid/duplicate transition identity: ' + str(manifest_path))
            continue
        ids.add(manifest['id'])
        seen = set()
        for entry in manifest.get('changed_inputs', []):
            path = Path(entry['current_path'])
            name = str(path)
            frozen = Path(entry['frozen_before'])
            if not path.is_absolute() or name in seen:
                errors.append('Invalid/duplicate transition output: ' + name)
                continue
            seen.add(name)
            previous = entry['previous_sha256']
            if name in expected and expected[name] != previous:
                errors.append('Transition breaks previous input chain: ' + name)
            if not frozen.is_file() or frozen.is_symlink() or sha(frozen) != previous:
                errors.append('Transition recovery input changed/missing: ' + str(frozen))
            if frozen.resolve() == path.resolve():
                errors.append('Recovery input aliases mutable source: ' + name)
            expected[name] = entry['sha256']
        for entry in manifest.get('added_sources', []):
            path = Path(entry['current_writer'])
            name = str(path)
            if not path.is_absolute() or name in expected or name in seen:
                errors.append('Duplicate/invalid added source authority: ' + name)
                continue
            if not entry.get('target_module') or not entry.get('source_role'):
                errors.append('Added source lacks owner/role: ' + name)
            expected[name] = entry['sha256']
            derived.append({**entry, 'transition_id': manifest['id']})
        for entry in manifest.get('added_nonproduction_inputs', []):
            path = Path(entry['current_path'])
            name = str(path)
            if not path.is_absolute() or name in expected or name in seen:
                errors.append('Duplicate/invalid added input: ' + name)
                continue
            expected[name] = entry['sha256']
    for name, digest in expected.items():
        path = Path(name)
        if not path.is_file() or sha(path) != digest:
            errors.append('Missing/changed current input: ' + name)
    canonical = set()
    for row in [*state['production_sources'], *derived]:
        path = str(Path(row['current_writer']).resolve())
        if path in canonical:
            errors.append('Duplicate production source authority: ' + path)
        canonical.add(path)
    source_root = state.get('source_root')
    if source_root:
        for path in (Path(source_root) / 'move').glob('*/sources/*.move'):
            # Separate historical V8 tree; its original duty queue is retained.
            # The current target baseline intentionally contains nine packages.
            if path.parent.parent.name == 'soulidity':
                continue
            if str(path.resolve()) not in canonical:
                errors.append('Unmapped production source: ' + str(path))
    return expected, derived, errors
