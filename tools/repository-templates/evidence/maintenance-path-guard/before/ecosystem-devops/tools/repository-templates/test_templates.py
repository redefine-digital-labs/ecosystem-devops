#!/usr/bin/env python3
"""Exercise artifact generation and meaningful rejection gates in temporary repositories."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def run(argv, expected=0):
    result = subprocess.run([sys.executable, *map(str, argv)], text=True, capture_output=True)
    if (result.returncode == 0) != (expected == 0):
        raise AssertionError(f"unexpected result for {argv}: {result.stdout} {result.stderr}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    args = parser.parse_args()
    out = Path(tempfile.mkdtemp(prefix="soulidity-ten-repo-check-")) / "repositories"
    run([HERE / "generate.py", "--source-root", args.source_root, "--output", out])
    run([HERE / "verify_generated.py", out])
    manifest = json.loads((out / "generation-manifest.json").read_text())
    configs = [json.loads((out / m["repository"] / "module.json").read_text()) for m in manifest["modules"]]
    assert len(configs) == 10
    assert sum(len(c["agent_contract"]) for c in configs) == 100
    assert sum(len(c["management"]["responsibility_mappings"]) for c in configs) == 20
    assert sum(len(c["engineering_permissions"]) for c in configs) == 40
    kinds = [p["kind"] for c in configs for p in c["pipelines"]]
    assert kinds.count("ci") == 10 and kinds.count("version_release") == 9 and kinds.count("cross_repository_integration") == 1
    checks = ["ten_artifacts_and_executable_contract_ci", "100_agent_fields_20_mappings_40_permissions_20_pipelines"]
    repo = out / "soul-sdk"
    config_file = repo / "module.json"
    baseline = config_file.read_bytes()
    original = json.loads(baseline)

    def rejects(name, mutate=None, argv=None):
        candidate = copy.deepcopy(original)
        if mutate:
            mutate(candidate)
            config_file.write_text(json.dumps(candidate, ensure_ascii=False))
        try:
            run([repo / "scripts/ci.py", *(argv or [])], expected=1)
            checks.append(name)
        finally:
            config_file.write_bytes(baseline)

    rejects("missing_agent_field_rejected", lambda c: c["agent_contract"].pop("budget"))
    rejects("cross_repository_write_scope_rejected", lambda c: c["write_boundary"].update(writable_paths=["../soul-market/**"]))
    rejects("cross_repository_changed_path_rejected", argv=["--changed-path", "../soul-market/src/order.move"])
    rejects("upgrade_role_is_not_runtime_authority", lambda c: c["engineering_capabilities"].update(upgrade_authority_grants_runtime_authority=True))
    rejects("pending_identity_cannot_impersonate_account", lambda c: c["management"]["responsibility_mappings"]["maintenance"].update(actual_identity="CIPHER"))
    rejects("missing_stage_evidence_rejected", lambda c: c["delivery_attachment"]["stage_exit_criteria"][2].update(status="passed"))
    rejects("unregistered_product_checks_rejected", argv=["--product"])
    rejects("pending_release_rejected", argv=["--release-ready"])

    def self_review(c):
        assignments = c["management"]["responsibility_mappings"]
        for a in assignments.values():
            a.update(status="confirmed", actual_identity="same_executor", evidence=["actual assignment reference"])
        c["agent_contract"]["identity"].update(status="confirmed", actual_identity="same_executor")
    rejects("self_review_cannot_be_independent_acceptance", self_review)
    before = hashlib.sha256((out / "generation-manifest.json").read_bytes()).hexdigest()
    run([HERE / "generate.py", "--source-root", args.source_root, "--output", out], expected=1)
    assert before == hashlib.sha256((out / "generation-manifest.json").read_bytes()).hexdigest()
    checks.append("repeat_generation_does_not_overwrite")
    changed = json.loads(baseline)
    changed["purpose"] += " altered"
    config_file.write_text(json.dumps(changed, ensure_ascii=False))
    run([HERE / "verify_generated.py", out], expected=1)
    config_file.write_bytes(baseline)
    checks.append("receipt_detects_altered_generated_artifact")
    run([HERE / "verify_generated.py", out])
    receipt_path = out / "generation-manifest.json"
    receipt = receipt_path.read_bytes()
    drifted = json.loads(receipt)
    drifted["modules"][0]["module_id"] = "MARKET"
    receipt_path.write_text(json.dumps(drifted, ensure_ascii=False))
    run([HERE / "verify_generated.py", out], expected=1)
    receipt_path.write_bytes(receipt)
    checks.append("receipt_module_identity_drift_rejected")
    print(json.dumps({"status": "passed", "temporary_output": str(out), "checks": checks,
        "checks_count": len(checks), "repositories": 10, "deliverable_categories": 60,
        "actual_git_remote_chain_or_product_tests": False,
        "source_provenance": manifest["source_provenance"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, ValueError, OSError) as error:
        print(f"template verification failed: {error}", file=sys.stderr)
        sys.exit(1)
