#!/usr/bin/env python3
"""Offline integrity controls for actual source refactors; no Sui or RPC."""
import json
import tempfile
import unittest
from pathlib import Path
from source_transition_guard import sha, source_inputs


class TransitionControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='source-transition-control-')
        self.root = Path(self.temp.name)
        self.source = self.root / 'move/core/sources/custody.move'
        self.source.parent.mkdir(parents=True)
        self.source.write_text('baseline\n')
        self.before = self.root / 'recovery/custody.move'
        self.before.parent.mkdir()
        self.before.write_bytes(self.source.read_bytes())
        self.state = {'source_root': str(self.root), 'production_sources': [{
            'original': str(self.source), 'current_writer': str(self.source),
            'sha256': sha(self.source)}], 'packages': []}
        self.source.write_text('thin adapter\n')
        self.added = self.root / 'move/custody/sources/account.move'
        self.added.parent.mkdir(parents=True)
        self.added.write_text('sole implementation\n')
        self.manifest = {'schema': 1, 'id': 'custody-cut', 'changed_inputs': [{
            'current_path': str(self.source), 'previous_sha256': sha(self.before),
            'frozen_before': str(self.before), 'sha256': sha(self.source)}],
            'added_sources': [{'current_writer': str(self.added), 'sha256': sha(self.added),
                              'target_module': 'NATIVE.PRODUCER', 'source_role': 'implementation'}]}
        self.manifest_path = self.root / 'transition.json'
        self.refresh()

    def tearDown(self):
        self.temp.cleanup()

    def refresh(self):
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.state['source_transitions'] = [{
            'path': str(self.manifest_path), 'sha256': sha(self.manifest_path)}]

    def assert_rejected(self):
        self.assertTrue(source_inputs(self.state)[2])

    def test_adapter_and_added_implementation(self):
        expected, derived, errors = source_inputs(self.state)
        self.assertEqual(errors, [])
        self.assertEqual(expected[str(self.source)], sha(self.source))
        self.assertEqual(len(derived), 1)
        self.assertEqual(self.state['production_sources'][0]['sha256'], sha(self.before))

    def test_unchanged_baseline(self):
        self.source.write_bytes(self.before.read_bytes())
        self.added.unlink()
        self.state.pop('source_transitions')
        self.assertEqual(source_inputs(self.state)[2], [])

    def test_unrecorded_mutation(self):
        self.state.pop('source_transitions')
        self.assert_rejected()

    def test_output_changes_after_capture(self):
        self.source.write_text('unexpected mutation')
        self.assert_rejected()

    def test_added_source_changes_after_capture(self):
        self.added.write_text('unexpected mutation')
        self.assert_rejected()

    def test_recovery_changes(self):
        self.before.write_text('bad recovery')
        self.assert_rejected()

    def test_recovery_is_missing(self):
        self.before.unlink()
        self.assert_rejected()

    def test_recovery_symlink(self):
        saved = self.root / 'saved.move'
        saved.write_bytes(self.before.read_bytes())
        self.before.unlink()
        self.before.symlink_to(saved)
        self.assert_rejected()

    def test_recovery_aliases_output(self):
        entry = self.manifest['changed_inputs'][0]
        entry['frozen_before'] = str(self.source)
        entry['previous_sha256'] = sha(self.source)
        self.refresh()
        self.assert_rejected()

    def test_bad_previous_hash(self):
        self.manifest['changed_inputs'][0]['previous_sha256'] = '0' * 64
        self.refresh()
        self.assert_rejected()

    def test_manifest_hash_mismatch(self):
        self.manifest_path.write_text('{}')
        self.assert_rejected()

    def test_missing_manifest(self):
        self.manifest_path.unlink()
        self.assert_rejected()

    def test_duplicate_transition_identity(self):
        self.state['source_transitions'] *= 2
        self.assert_rejected()

    def test_duplicate_output(self):
        self.manifest['changed_inputs'] *= 2
        self.refresh()
        self.assert_rejected()

    def test_duplicate_derived_authority(self):
        self.manifest['added_sources'] *= 2
        self.refresh()
        self.assert_rejected()

    def test_derived_aliases_original(self):
        self.added.unlink()
        self.added.symlink_to(self.source)
        self.manifest['added_sources'][0]['sha256'] = sha(self.added)
        self.refresh()
        self.assert_rejected()

    def test_unmapped_new_module(self):
        (self.added.parent / 'hidden.move').write_text('hidden')
        self.assert_rejected()

    def test_unmapped_new_package(self):
        source = self.root / 'move/hidden/sources/hidden.move'
        source.parent.mkdir(parents=True)
        source.write_text('hidden')
        self.assert_rejected()

    def test_two_sequential_transformations(self):
        previous = self.root / 'recovery/adapter-v1.move'
        previous.write_bytes(self.source.read_bytes())
        self.source.write_text('adapter v2')
        path = self.root / 'transition2.json'
        path.write_text(json.dumps({'schema': 1, 'id': 'second', 'changed_inputs': [{
            'current_path': str(self.source), 'previous_sha256': sha(previous),
            'frozen_before': str(previous), 'sha256': sha(self.source)}]}))
        self.state['source_transitions'].append({'path': str(path), 'sha256': sha(path)})
        self.assertEqual(source_inputs(self.state)[2], [])

    def add_manifest(self):
        path = self.added.parent.parent / 'Move.toml'
        path.write_text('frozen dependency locator')
        self.manifest['added_nonproduction_inputs'] = [{
            'current_path': str(path), 'sha256': sha(path)}]
        self.refresh()
        return path

    def test_added_dependency_manifest(self):
        self.add_manifest()
        self.assertEqual(source_inputs(self.state)[2], [])

    def test_added_manifest_changed(self):
        self.add_manifest().write_text('unexpected dependency replacement')
        self.assert_rejected()

    def test_added_manifest_missing(self):
        self.add_manifest().unlink()
        self.assert_rejected()

    def test_added_manifest_duplicates_source(self):
        self.manifest['added_nonproduction_inputs'] = [{
            'current_path': str(self.added), 'sha256': sha(self.added)}]
        self.refresh()
        self.assert_rejected()


if __name__ == '__main__':
    unittest.main(verbosity=2)
