#!/usr/bin/env python3
"""Offline integrity controls for actual source refactors; no Sui or RPC."""
import json
import os
import subprocess
import sys
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


    def package_recovery(self):
        package = self.root / 'package'
        package.mkdir()
        (package / 'Move.toml').write_text('original manifest')
        (package / 'source.move').write_text('original source')
        frozen = self.root / 'package-recovery'
        frozen.mkdir()
        inputs = {}
        for path in package.iterdir():
            (frozen / path.name).write_bytes(path.read_bytes())
            inputs[path.name] = sha(path)
        row = {'package': 'prepared', 'canonical_candidate': str(package),
               'baseline_inputs': inputs.copy(), 'candidate_inputs': inputs.copy(),
               'state': 'active-source', 'frozen_before': str(frozen)}
        self.state['packages'] = [row]
        return package, frozen, row

    def test_whole_package_recovery_valid(self):
        self.package_recovery()
        self.assertEqual(source_inputs(self.state)[2], [])

    def test_whole_package_recovery_source_changed(self):
        _, frozen, _ = self.package_recovery()
        (frozen / 'source.move').write_text('corrupt recovery source')
        self.assert_rejected()

    def test_whole_package_recovery_manifest_changed(self):
        _, frozen, _ = self.package_recovery()
        (frozen / 'Move.toml').write_text('corrupt recovery dependency')
        self.assert_rejected()

    def test_whole_package_recovery_root_missing(self):
        _, _, row = self.package_recovery()
        row.pop('frozen_before')
        self.assert_rejected()

    def test_whole_package_recovery_file_missing(self):
        _, frozen, _ = self.package_recovery()
        (frozen / 'source.move').unlink()
        self.assert_rejected()

    def test_whole_package_recovery_symlink(self):
        package, frozen, _ = self.package_recovery()
        (frozen / 'source.move').unlink()
        (frozen / 'source.move').symlink_to(package / 'source.move')
        self.assert_rejected()

    def test_whole_package_recovery_current_root(self):
        package, _, row = self.package_recovery()
        row['frozen_before'] = str(package)
        self.assert_rejected()

    def test_whole_package_recovery_hardlink(self):
        package, frozen, _ = self.package_recovery()
        (frozen / 'source.move').unlink()
        os.link(package / 'source.move', frozen / 'source.move')
        self.assertTrue(any('aliases mutable' in message for message in source_inputs(self.state)[2]))

    def file_extraction(self, kind):
        target = self.root / ('client.ts' if kind == 'client_source_extractions' else 'content.move')
        target.write_text('original unchanged input')
        frozen = self.root / (target.name + '.recovery')
        frozen.write_bytes(target.read_bytes())
        old = self.root / (target.name + '.old')
        old.symlink_to(target)
        row = {'original': str(old), 'canonical': str(target), 'frozen_before': str(frozen), 'sha256': sha(target)}
        self.state[kind] = [{'modules': [row]}]
        return target, frozen, row

    def test_partial_file_recovery_valid(self):
        self.file_extraction('partial_extractions')
        self.assertEqual(source_inputs(self.state)[2], [])

    def test_partial_file_recovery_symlink(self):
        target, frozen, _ = self.file_extraction('partial_extractions')
        frozen.unlink()
        frozen.symlink_to(target)
        self.assert_rejected()

    def test_partial_file_recovery_current_input(self):
        target, _, row = self.file_extraction('partial_extractions')
        row['frozen_before'] = str(target)
        self.assert_rejected()

    def test_client_file_recovery_valid(self):
        self.file_extraction('client_source_extractions')
        self.assertEqual(source_inputs(self.state)[2], [])

    def test_client_file_recovery_symlink(self):
        target, frozen, _ = self.file_extraction('client_source_extractions')
        frozen.unlink()
        frozen.symlink_to(target)
        self.assert_rejected()

    def test_client_file_recovery_current_input(self):
        target, _, row = self.file_extraction('client_source_extractions')
        row['frozen_before'] = str(target)
        self.assert_rejected()

    def test_client_file_recovery_missing(self):
        _, frozen, _ = self.file_extraction('client_source_extractions')
        frozen.unlink()
        self.assert_rejected()

    def test_client_current_input_changed(self):
        target, _, _ = self.file_extraction('client_source_extractions')
        target.write_text('changed without transition')
        self.assert_rejected()

    def build_runner(self, mutate_stage=None, mutate_file='Move.toml'):
        package, frozen, row = self.package_recovery()
        lock = package / 'Move.lock'
        lock.write_text('frozen original lock')
        (frozen / lock.name).write_bytes(lock.read_bytes())
        row['baseline_inputs'][lock.name] = sha(lock)
        row['candidate_inputs'][lock.name] = sha(lock)
        manifest = package / 'Move.toml'
        previous = sha(manifest)
        manifest.write_text('registered current manifest')
        self.manifest['changed_inputs'].append({'current_path': str(manifest), 'previous_sha256': previous,
            'frozen_before': str(frozen / manifest.name), 'sha256': sha(manifest)})
        self.refresh()
        workspace = self.root / 'workspace'
        workspace.mkdir()
        (workspace / 'workspace.json').write_text(json.dumps(self.state))
        fake = self.root / 'fake-sui'
        fake.write_text('#!' + sys.executable + '\nimport sys\nfrom pathlib import Path\n'
            + "if '--version' in sys.argv:\n print('offline-control-tool');sys.exit(0)\n"
            + 'stage=' + repr(mutate_stage) + '\n'
            + 'if stage is not None and stage in sys.argv:\n Path(' + repr(str(package / mutate_file))
            + ").write_text('unexpected build/test mutation')\n"
            + "print('{}')\n")
        fake.chmod(0o700)
        command = [sys.executable, str(Path(__file__).parent / 'build_repository_packages.py'),
            '--workspace', str(workspace), '--sui', str(fake), '--package', 'prepared']
        process = subprocess.run(command, capture_output=True, text=True)
        evidence = json.loads((workspace / 'build-evidence/prepared/evidence.json').read_text())
        self.assertIn('--install-dir', evidence['command'])
        self.assertIn('--install-dir', evidence['test_command'])
        self.assertEqual(evidence['exit_code'], 0)
        return process, evidence, row

    def test_build_runner_accepts_latest_registered_input(self):
        process, evidence, row = self.build_runner()
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(evidence['input_errors_after_build'], [])
        self.assertEqual(evidence['input_errors_after_test'], [])
        self.assertNotEqual(evidence['candidate_inputs']['Move.toml'], row['candidate_inputs']['Move.toml'])
        self.assertEqual(row['baseline_inputs'], row['candidate_inputs'])

    def test_build_runner_rejects_build_manifest_mutation(self):
        process, evidence, _ = self.build_runner('build')
        self.assertNotEqual(process.returncode, 0)
        self.assertTrue(evidence['input_errors_after_build'])
        self.assertIsNone(evidence['test_exit_code'])

    def test_build_runner_rejects_build_lock_mutation(self):
        process, evidence, _ = self.build_runner('build', 'Move.lock')
        self.assertNotEqual(process.returncode, 0)
        self.assertTrue(evidence['input_errors_after_build'])

    def test_build_runner_rejects_test_lock_mutation(self):
        process, evidence, _ = self.build_runner('test', 'Move.lock')
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(evidence['input_errors_after_build'], [])
        self.assertEqual(evidence['test_exit_code'], 0)
        self.assertTrue(evidence['input_errors_after_test'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
