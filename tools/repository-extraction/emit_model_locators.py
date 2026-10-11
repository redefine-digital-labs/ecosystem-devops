"""Emit reviewable local development manifests; never mutate source repositories.

All Model providers use the retained source-root/move locators as resolver
identities. All Model consumers use its real new repository directory.
Re-run this generator if either checkout moves. This is not a release pin.
"""
from pathlib import Path
import argparse, hashlib, json, os, re

parser = argparse.ArgumentParser()
parser.add_argument('--authority-root', required=True)
parser.add_argument('--ecosystem-root', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()
authority = Path(args.authority_root).resolve()
ecosystem = Path(args.ecosystem_root).resolve()
out = Path(args.output).resolve()
model = ecosystem / 'soul-extensions' / 'move' / 'soulidity_model'
changes = []

def change(path, replacements, output_relative):
    before = path.read_text()
    after = before
    for name, provider in replacements.items():
        locator = os.path.relpath(provider, path.parent)
        pattern = r'(^' + re.escape(name) + r'\s*=\s*\{\s*local\s*=\s*")[^"]+("\s*\}.*$)'
        after, count = re.subn(pattern, lambda m: m.group(1) + locator + m.group(2), after, flags=re.M)
        assert count == 1, (path, name, count)
        normalized = Path(os.path.abspath(path.parent / locator))
        assert normalized == provider, (normalized, provider)
    target = out / output_relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(after)
    baseline = out / 'before' / output_relative
    baseline.parent.mkdir(parents=True, exist_ok=True)
    baseline.write_text(before)
    changes.append({'target': str(path), 'candidate': str(target), 'baseline': str(baseline),
                    'before_sha256': hashlib.sha256(before.encode()).hexdigest(),
                    'after_sha256': hashlib.sha256(after.encode()).hexdigest(),
                    'changed_dependency_names': list(replacements)})

change(model / 'Move.toml', {name: authority / 'move' / package for name, package in [
    ('SoulidityStandard', 'soulidity_standard'), ('SoulidityFoundation', 'soulidity_foundation'),
    ('SoulidityVisual', 'soulidity_visual')]}, Path('soul-extensions/move/soulidity_model/Move.toml'))
for name in ['soulidity_v1', 'soulidity_application', 'standard_examples/model_producer']:
    change(authority / 'move' / name / 'Move.toml', {'SoulidityModel': model}, Path('retained/move') / name / 'Move.toml')
out.mkdir(parents=True, exist_ok=True)
(out / 'payload.json').write_text(json.dumps({'kind': 'generated-local-development-path-locators',
    'authority_root': str(authority), 'ecosystem_root': str(ecosystem), 'changes': changes,
    'source_code_changes': 0, 'publication_or_remote_release_pin': False,
    'portability': 'Regenerate these direct relative paths for the actual checkout layout; do not import them into remote release CI as immutable pins.'}, indent=2) + '\n')
print(json.dumps({'output': str(out), 'manifest_count': len(changes)}, indent=2))
