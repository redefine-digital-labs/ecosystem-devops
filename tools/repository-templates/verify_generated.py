#!/usr/bin/env python3
"""Check generated repository artifacts and their immutable generation receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def verify(root):
    manifest = json.loads((root / "generation-manifest.json").read_text())
    if manifest["actual_git_or_remote_creation"] is not False:
        raise ValueError("scaffolds must not assert actual Git or remote creation")
    modules = manifest["modules"]
    repositories = {m["repository"] for m in modules}
    if not modules or len(repositories) != len(modules):
        raise ValueError("duplicate generated repository identities")
    checked = []
    for item in modules:
        repo = root / item["repository"]
        if not repo.resolve().is_relative_to(root.resolve()) or (repo / ".git").exists():
            raise ValueError("generated artifact escaped output root or created Git metadata")
        config = json.loads((repo / "module.json").read_text())
        if config["module_id"] != item["module_id"] or config["repository"] != item["repository"]:
            raise ValueError("generation receipt module identity differs from repository contract")
        if config["source_provenance"] != manifest["source_provenance"]:
            raise ValueError("generation receipt source provenance differs from repository contract")
        for name, expected in item["files"].items():
            path = repo / name
            if not path.resolve().is_relative_to(repo.resolve()) or not path.is_file():
                raise ValueError(f"missing/escaped generated artifact: {name}")
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f"generated artifact hash changed: {repo.name}/{name}")
        run = subprocess.run([sys.executable, str(repo / "scripts/ci.py")], capture_output=True, text=True)
        if run.returncode:
            raise ValueError(f"{repo.name}: {run.stderr.strip()}")
        checked.append(item["module_id"])
    print(json.dumps({"maintenance_artifacts_verified": checked, "count": len(checked),
        "scope": "generation hashes and executable maintenance contract validation",
        "product_build_or_runtime_verified": False}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        verify(args.output.resolve())
    except (KeyError, TypeError, ValueError, OSError) as error:
        print(f"generation verification failed: {error}", file=sys.stderr)
        sys.exit(1)
