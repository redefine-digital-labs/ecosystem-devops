#!/usr/bin/env python3
"""Build and test prepared packages offline, without publication or signing."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--sui', type=Path, required=True)
    parser.add_argument('--package')
    parser.add_argument('--round', default='')
    args = parser.parse_args()
    state = json.loads((args.workspace / 'workspace.json').read_text())
    version = subprocess.run([str(args.sui), '--version'], check=True, capture_output=True, text=True).stdout.strip()
    failed = False
    for row in state['packages']:
        if args.package and row['package'] != args.package:
            continue
        package = Path(row['canonical_candidate'])
        directory = args.workspace / 'build-evidence' / (row['package'] + args.round)
        if directory.exists():
            raise SystemExit(f'Refuse to overwrite build evidence: {directory}')
        directory.mkdir(parents=True)
        actual = {rel: digest(package / rel) for rel in row['candidate_inputs']}
        if actual != row['candidate_inputs']:
            raise SystemExit(f"Unfrozen candidate: {row['package']}")
        command = [str(args.sui), 'move', 'build', '--path', str(package),
                   '--dump-bytecode-as-base64', '--no-tree-shaking', '--with-unpublished-dependencies']
        build = subprocess.run(command, capture_output=True)
        (directory / 'build.json').write_bytes(build.stdout)
        (directory / 'build.log').write_bytes(build.stderr)
        test_command = [str(args.sui), 'move', 'test', '--path', str(package)]
        if build.returncode == 0:
            test = subprocess.run(test_command, capture_output=True)
            (directory / 'test.log').write_bytes(test.stdout + test.stderr)
            test_code = test.returncode
        else:
            test_code = None
        result = {'package': row['package'], 'candidate_path': str(package),
                  'candidate_inputs': actual, 'tool': str(args.sui),
                  'tool_sha256': digest(args.sui), 'tool_version': version,
                  'command': command, 'exit_code': build.returncode,
                  'test_command': test_command, 'test_exit_code': test_code,
                  'build_sha256': digest(directory / 'build.json'),
                  'log_sha256': digest(directory / 'build.log'),
                  'signed_transactions': 0, 'deployed': False}
        if (directory / 'test.log').exists():
            result['test_log_sha256'] = digest(directory / 'test.log')
        (directory / 'evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        row['build_evidence'] = str(directory / 'evidence.json')
        (args.workspace / 'workspace.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'package': row['package'], 'build': build.returncode, 'test': test_code}), flush=True)
        failed |= build.returncode != 0 or test_code != 0
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
