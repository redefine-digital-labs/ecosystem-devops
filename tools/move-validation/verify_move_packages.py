#!/usr/bin/env python3
"""Verify declared repository Move packages without RPC, publication or signing."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

SUI_SHA256 = '1d7baa7c7314113671415acfa20279b1eedb6ae6d04f286988a00da285e769c3'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs(package):
    paths = [package / 'Move.toml']
    if (package / 'Move.lock').exists():
        paths.append(package / 'Move.lock')
    for folder in ['sources', 'tests']:
        paths += sorted((package / folder).rglob('*.move'))
    return {str(p.relative_to(package)): sha(p) for p in paths}


def execute(argv, log):
    try:
        completed = subprocess.run(argv, capture_output=True, timeout=300)
        output = completed.stdout + completed.stderr
        code = completed.returncode
    except subprocess.TimeoutExpired as failure:
        output = (failure.stdout or b'') + (failure.stderr or b'') + b'\nTIMEOUT\n'
        code = 124
    log.write_bytes(output)
    return {'argv': argv, 'exit_code': code, 'log': str(log), 'log_sha256': sha(log)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', action='append', required=True,
                        help='repository-relative package path; repeatable')
    parser.add_argument('--minimum-tests', type=int, required=True,
                        help='minimum across declared packages; zero cannot prove behavior')
    parser.add_argument('--sui', type=Path, default=os.environ.get('SUI_BINARY'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if root.name == 'move-validation':
        parser.error('Install this pinned tool in the consumer repository scripts directory')
    if args.minimum_tests < 0:
        parser.error('--minimum-tests must be nonnegative')
    if not args.sui or not args.sui.is_file() or sha(args.sui) != SUI_SHA256:
        parser.error('SUI_BINARY/--sui must identify the exact pinned CLI SHA256')
    packages = []
    for relative in args.package:
        package = root / relative
        if package.is_symlink() or not package.resolve().is_relative_to(root):
            parser.error('Package must be an owned in-repository directory')
        if not (package / 'Move.toml').is_file():
            parser.error('Missing package manifest: ' + relative)
        packages.append(package)
    directory = root / 'output'
    directory.mkdir(exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='move-check-', dir=directory))
    report = {'result': 'FAIL', 'tool_sha256': sha(args.sui),
              'packages': [], 'transactions': 0, 'remote_execution': False,
              'deployment': False, 'minimum_tests': args.minimum_tests}
    all_passed = True
    total = 0
    for index, package in enumerate(packages):
        out = run / str(index)
        out.mkdir()
        row = {'package': str(package.relative_to(root)), 'inputs_before': inputs(package)}
        base = [str(args.sui), 'move']
        row['build'] = execute(base + ['build', '--path', str(package), '--install-dir',
                                     str(out / 'production')], out / 'production.log')
        row['test'] = None
        if row['build']['exit_code'] == 0:
            row['test'] = execute(base + ['test', '--path', str(package), '--install-dir',
                                        str(out / 'test')], out / 'tests.log')
            log = (out / 'tests.log').read_text(errors='replace')
            match = re.search(r'Test result: (\w+)\. Total tests: (\d+); passed: (\d+); failed: (\d+)', log)
            row['test']['summary'] = ({'result': match[1], 'total': int(match[2]),
                                      'passed': int(match[3]), 'failed': int(match[4])}
                                     if match else None)
            summary = row['test']['summary']
            row['passed'] = (row['test']['exit_code'] == 0 and summary is not None
                             and summary['failed'] == 0 and summary['total'] == summary['passed']
                             and summary['result'] == 'OK')
            if summary:
                total += summary['passed']
        else:
            row['passed'] = False
        row['inputs_after'] = inputs(package)
        row['source_and_manifest_unchanged'] = (
            {path: value for path, value in row['inputs_before'].items() if path != 'Move.lock'}
            == {path: value for path, value in row['inputs_after'].items() if path != 'Move.lock'})
        row['passed'] = row['passed'] and row['source_and_manifest_unchanged']
        row['production_artifacts'] = {
            str(p.relative_to(out / 'production')): sha(p)
            for p in sorted((out / 'production').rglob('*.mv'))}
        report['packages'].append(row)
        all_passed = all_passed and row['passed']
    report['tests_passed'] = total
    report['scope'] = 'Production compile and declared VM regression; real published linkage and user journeys require separate evidence'
    report['result'] = 'PASS' if all_passed and total >= args.minimum_tests else 'FAIL'
    evidence = run / 'evidence.json'
    evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'result': report['result'], 'tests_passed': total,
                      'evidence': str(evidence)}, ensure_ascii=False))
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
