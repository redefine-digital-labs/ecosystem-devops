#!/usr/bin/env python3
"""Exercise artifact generation and meaningful rejection gates in temporary repositories."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def run(argv, expected=0):
    result = subprocess.run([sys.executable, *map(str, argv)], text=True, capture_output=True)
    if (result.returncode == 0) != (expected == 0):
        raise AssertionError(f"unexpected result for {argv}: {result.stdout} {result.stderr}")
    return result


def test_maintenance_boundaries(out, configs, checks):
    with tempfile.TemporaryDirectory(prefix="soulidity-maintenance-boundaries-") as temporary:
        for original in configs:
            repo = Path(temporary) / original["repository"]
            shutil.copytree(out / original["repository"], repo)
            config_file = repo / "module.json"
            config = copy.deepcopy(original)
            marker = repo / "product-command-ran"
            (repo / "scripts/product_probe.py").write_text(
                "from pathlib import Path\nPath('product-command-ran').write_text('ran')\n")
            config["ci"]["product_commands"] = [{"id": "guard-control-flow-probe",
                "argv": [sys.executable.split('/')[-1], "scripts/product_probe.py"]}]

            def check(name, path, error=None, candidate=None, product=True):
                config_file.write_text(json.dumps(candidate or config, ensure_ascii=False))
                marker.unlink(missing_ok=True)
                result = run([repo / "scripts/ci.py", "--changed-path", path,
                              *(["--product"] if product else [])], expected=1 if error else 0)
                if error:
                    assert error in result.stderr, result.stderr
                    assert not marker.exists(), "rejected path executed a product command"
                    assert '"maintenance_contract": "passed"' not in result.stdout
                else:
                    summary = json.loads(result.stdout.splitlines()[-1])
                    assert summary["maintenance_contract"] == "passed"
                    assert summary["product_checks"] == ("passed" if product else "not_run_by_this_command")
                    assert summary["remote_execution_or_deployment_verified"] is False
                    assert marker.exists() is product
                checks.append(f"{original['repository']}:{name}")

            check("own_sources_allowed_before_product", "sources/owned.move")
            check("structure_only_does_not_run_product", "sources/owned.move", product=False)
            for path in [".deps/dependency/sources/readonly.move", "candidate-dependencies/pin/source.move",
                         "evidence/extraction-original/baseline.move"]:
                check(f"read_only_rejected:{path}", path, "changed path is read-only")
            if original["module_id"] not in {"SDK", "CONTENT"}:
                continue
            for path in [".deps", "candidate-dependencies", "./.deps/source.move",
                         ".deps//source.move"]:
                check(f"read_only_alias_rejected:{path}", path, "changed path is read-only")
            for path in ["../soul-market/sources/order.move", "sources/../../soul-market/order.move",
                         str(repo.parent / "soul-market/sources/order.move"), "C:/soul-market/order.move"]:
                check(f"external_path_rejected:{path}", path, "path escapes repository boundary")
            narrow = copy.deepcopy(config)
            narrow["write_boundary"]["writable_paths"] = ["sources/**"]
            narrow["agent_contract"]["write_scope"]["paths"] = ["sources/**"]
            check("narrow_own_sources_allowed", "./sources/owned.move", candidate=narrow)
            check("outside_declared_scope_rejected", "docs/unowned.md",
                  "changed path is outside module write scope", candidate=narrow)
            (repo / "sources").mkdir()
            (repo / "sources/unowned-alias").symlink_to("../docs", target_is_directory=True)
            check("local_alias_outside_declared_scope_rejected", "sources/unowned-alias/unowned.md",
                  "changed path is outside module write scope", candidate=narrow)
            (repo / "sources/unowned-alias").unlink()
            for field, path in [("non_writable_paths", "evidence/extraction-original/baseline.move"),
                                ("read_only_dependency_paths", ".deps/source.move")]:
                isolated = copy.deepcopy(config)
                if field == "non_writable_paths":
                    isolated["agent_contract"]["write_scope"]["read_only_dependency_paths"] = []
                else:
                    isolated["write_boundary"]["non_writable_paths"] = []
                check(f"{field}_independently_enforced", path, "changed path is read-only", candidate=isolated)
            invalid_deny = copy.deepcopy(config)
            invalid_deny["agent_contract"]["write_scope"]["read_only_dependency_paths"] = ["../soul-market/**"]
            check("external_deny_declaration_rejected", "sources/owned.move",
                  "path escapes repository boundary", candidate=invalid_deny)
            (repo / ".deps").mkdir()
            (repo / "dependency-alias").symlink_to(".deps", target_is_directory=True)
            check("local_alias_to_dependency_rejected", "dependency-alias/source.move", "changed path is read-only")
            (repo / "dependency-alias").unlink()
            (repo / "external-alias").symlink_to(repo.parent / "soul-market", target_is_directory=True)
            check("symlink_to_other_repository_rejected", "external-alias/source.move", "changed path escapes repository boundary")
            (repo / "external-alias").unlink()
            if original["module_id"] == "CONTENT":
                check("content_owned_package_alias_allowed", "packages/soulidity_content/sources/owned.move")
                check("content_own_sources_allowed", "sources/soulidity_content/owned.move")
                for prefix in ["packages/soulidity_standard", "packages/soulidity_foundation", "offline-vendor", "frozen-original"]:
                    for path in [prefix, f"{prefix}/sources/readonly.move"]:
                        check(f"content_dependency_rejected:{path}", path, "changed path is read-only")


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
    test_maintenance_boundaries(out, configs, checks)
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
