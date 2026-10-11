#!/usr/bin/env python3
"""Exact source ownership map; design responsibility is not migration evidence."""
import argparse
import hashlib
import json
from pathlib import Path

TARGETS = {
    'STANDARD': {'soulidity_standard': ['soul']},
    'CONTENT': {'soulidity_content': ['authority', 'authorization', 'blob_custody', 'document', 'kind_registry', 'paid_access', 'paged_store', 'permissions', 'storage']},
    'MAKER': {'soulidity_application': ['issuance', 'publication_rules', 'physical_metadata', 'resale'],
              'soulidity_v1': ['catalog', 'release', 'player', 'runtime', 'issuer', 'metadata', 'physical', 'collection']},
    'CHANNEL': {},
    'MARKET': {'soulidity_v1': ['market']},
    'EXTENSIONS': {'soulidity_model': ['assembly', 'components', 'material_policy', 'policy'],
        'soulidity_visual': ['visual'],
        'soulidity_application': ['character', 'forms', 'growth', 'output', 'vault', 'visual_capture'],
        'soulidity_content': ['loadout', 'state_configuration'],
        'soulidity_v1': ['access', 'application_operator']},
    'COMMUNITY': {'soulidity_community': ['profile', 'social', 'community_posts', 'community_votes']},
    'NATIVE.PRODUCER': {'soulidity_native': ['birth', 'registry'], 'soulidity_content': ['founding_library'],
        'soulidity_v1': ['native_binding', 'native_creation', 'custody']},
    'POLICY.ASSET_RULES': {'soulidity_foundation': ['economics', 'revenue', 'source_authority']},
    'POLICY.PACKAGE_GOVERNANCE': {'soulidity_foundation': ['package_roles']},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    state = json.loads((args.workspace / 'workspace.json').read_text())
    source, design = Path(state['source_root']), Path(state['design_root'])
    index = json.loads((source / 'output/ecosystem-construction/gate0-2026-10-10/gate0-inventory/module-and-retained-source-selectors.json').read_text())
    units = {row['id']: row for row in index['rows']}
    repository_by_module = {row['id']: row['local_path'] for row in state['repositories']}
    targets = {}
    for owner, packages in TARGETS.items():
        for package, modules in packages.items():
            for module in modules:
                relative = f'move/{package}/sources/{module}.move'
                if relative in targets:
                    raise SystemExit(f'Double source owner: {relative}')
                targets[relative] = owner
    rows = []
    for original in state['production_sources']:
        relative = str(Path(original['original']).relative_to(source))
        owner = targets.pop(relative)
        canonical = Path(original['current_writer']).resolve()
        authority_repo = next((name for name, root in repository_by_module.items()
                               if canonical.is_relative_to(Path(root))), 'retained:soulidity')
        rows.append({**original, 'relative_original': relative, 'target_module': owner,
            'target_repository': repository_by_module.get(owner, str(source)),
            'actual_source_repository': authority_repo, 'canonical_current_writer': str(canonical),
            'proposed_maintenance': units[owner]['source_contract'].get('maintenance_mapping', 'preserve original owner'),
            'actual_owner': 'original record Owner retained; this mapping does not reassign',
            'chain_type_migrated': False})
    if targets or len(rows) != 52:
        raise SystemExit('Source mapping is not exact')
    retained = [{**units[key]['source_contract'], 'source_rows': [r['relative_original'] for r in rows if r['target_module'] == key],
        'current_source_locations': [r['canonical_current_writer'] for r in rows if r['target_module'] == key],
        'actual_owner': 'preserve original owner', 'independent_release_verified': False}
        for key in units if '.' in key]
    if len(retained) != 15:
        raise SystemExit('Expected exactly 15 retained maintenance units')
    trace = design / 'docs/open-ecosystem/ORIGINAL_SCOPE_TRACE.json'
    coverage = source / 'docs/CONTRACT_REBUILD_COVERAGE.json'
    data = {'schema': 1, 'modules': 10, 'retained_maintenance_units': retained,
        'production_sources': rows, 'production_sources_count': len(rows),
        'missing_channel_implementation': True,
        'original_scope_reference': {'path': str(trace), 'sha256': sha(trace), 'records': 157},
        'original_review_queue_reference': {'path': str(coverage), 'sha256': sha(coverage),
            'existing_status_unchanged': True},
        'corrections_to_old_selectors': {
            'previously_unmapped_sources': ['physical_metadata', 'custody', 'access', 'runtime', 'application_operator', 'metadata'],
            'removed_double_writer_assignments': ['soulidity_model::policy', 'soulidity_model::material_policy']},
        'mixed_package_blockers': [
            {'package': 'soulidity_content', 'units': ['CONTENT', 'EXTENSIONS', 'NATIVE.PRODUCER'],
             'next': 'Separate state/loadout/founding responsibility through actual public contracts; keep source singular until verified'},
            {'package': 'soulidity_application', 'units': ['MAKER', 'EXTENSIONS'],
             'next': 'Separate issuance/economic policy from selected application schema without dropping existing rights'},
            {'package': 'soulidity_v1', 'units': ['MAKER', 'EXTENSIONS', 'NATIVE.PRODUCER', 'MARKET'],
             'next': 'Extract complete Market first; then remove producer/operator/custody cycles with real authority contracts'}],
        'not_second_task_board': True,
        'not_proof_of': ['business decoupling', 'runtime permission paths', 'chain cutover', 'full product acceptance']}
    (args.workspace / 'source-authority.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('Exact ownership map: 52/52 unique sources, 10 target repositories, 15 retained units; Channel implementation missing.')


if __name__ == '__main__':
    main()
