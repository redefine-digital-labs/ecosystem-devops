#!/usr/bin/env python3
"""Generate bounded repository scaffolds from the existing design registry."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
SOURCES = {
    "spec": "docs/SOULIDITY_ECOSYSTEM_MODULARIZATION_SPEC_CN.md",
    "agent_fields": "docs/SOULIDITY_CONTRACT_MODULES_AND_PERMISSION_BOUNDARIES_CN.md",
    "plan": "docs/open-ecosystem/MODULE_DELIVERY_PLAN.json",
    "contracts": "docs/open-ecosystem/MODULE_INTEROPERABILITY_CONTRACTS.json",
    "scope": "docs/open-ecosystem/ORIGINAL_SCOPE_TRACE.json",
    "registry": "agent-management/workspace.json",
    "operating_model": "agent-management/OPERATING_MODEL.md",
    "handbook": "agent-management/PRODUCT_ENGINEERING_HANDBOOK_CN.md",
}
STAGES = {
    "Plan": "The original record clearly defines the user outcome, sole Owner, actual acceptor, normal/failure/recovery conditions and Ready criteria",
    "Code": "Exact changes, independent review and relevant regressions; Implemented does not mean Released",
    "Build": "Pinned tools/dependencies/configuration and source/artifact hashes; explain the N/A reason when no build is required",
    "Test": "Exact combinations, normal/failure/recovery paths and applicable security counterexamples; untested items and original journey results are clear",
    "Release": "Applicable G3, a single manifest, independent acceptance, release responsibility, original authorization and recovery boundaries",
    "Deploy": "The exact target and G4 readback for the same candidate; do not mark complete while the original production operation awaits acceptance",
    "Operate": "Actual operational responsibility, applicable G5, recovery/reconciliation; query the original result of a successful transaction first",
    "Monitor": "Observation window/source/threshold basis and findings linked to the original DEV/BUG; unknowns are clear",
}
CONSUMER_FIELDS = ["provider_and_exact_interface", "used_actions_and_types",
    "supported_schema_and_behavior", "required_effects", "authority_and_state_inputs",
    "failure_exit_and_recovery", "version_combination_and_artifacts",
    "verification_and_migration_evidence"]
DEPENDENCY_FIELDS = ["consumer", "provider", "kind", "used_actions_types_state",
    "selection_condition", "exact_version_range", "change_validation", "exit_or_migration"]
DEPENDENCY_KINDS = ["compile", "runtime", "behavior", "authority", "funds", "state", "content"]
EXPECTED = {"SDK": "soul-sdk", "DEVOPS": "ecosystem-devops",
    "INTEGRATION": "ecosystem-integration", "STANDARD": "soul-standard",
    "CONTENT": "soul-content", "COMMUNITY": "soul-community", "MAKER": "maker-protocol",
    "CHANNEL": "soul-channel", "MARKET": "soul-market", "EXTENSIONS": "soul-extensions"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def registry_refs(registry):
    result = {}
    for label, key in [("Delivery", "delivery"), ("DEV", "product_development"),
                       ("BUG", "product_bugs")]:
        entry = registry[key]
        records = registry.get("task_records", []) if label == "Delivery" else entry["records"]
        result[label] = {"list_id": entry["id"], "url": entry["url"],
                         "records": [{k: r[k] for k in ("id", "record_id", "url")} for r in records]}
    return result


def make_config(plan, contract, sources, registry, scope):
    module = plan["id"]
    tool = module in {"SDK", "DEVOPS", "INTEGRATION"}
    records = []
    for record in scope["records"]:
        if module not in record["target_units"]:
            continue
        records.append({k: record[k] for k in ("id", "original_id", "record_id",
            "original_table", "original_list_id", "original_list_url", "owner_ref", "reviewer_ref")})
        records[-1]["linked_original_records_historical"] = record.get("original_row_historical", {}).get("关联原研发／Bug")
    pending = {"status": "pending", "actual_identity": None, "evidence": []}
    assignment = {"maintenance": dict(pending, role_recommendation=plan["maintenance_role_mapping_recommended"],
            original_owner_rule="Follow the original record's Owner; recommended roles do not replace active Owners"),
        "independent_acceptance": dict(pending, role_recommendation=contract["review_mapping"],
            qualification_evidence=[], independence_evidence=[],
            original_owner_rule="Follow the original record's acceptance responsibility; high-risk work is reviewed by a qualified, independent actual acceptor")}
    permissions = []
    for category in ["source_maintenance", "version_release", "production_deployment", "onchain_control"]:
        applicable = not ((tool and category == "onchain_control") or
            (module == "INTEGRATION" and category == "version_release"))
        permissions.append({"category": category, "applicability": "pending" if applicable else "not_applicable",
            "reason": None if applicable else ("Tool repositories have no business on-chain control" if tool and category == "onchain_control" else "Integration has no separate version release"),
            "effective_authority_paths": [], "actual_holder": None, "authorization_ref": None, "evidence": []})
    pipeline = "cross_repository_integration" if module == "INTEGRATION" else "version_release"
    dependency_paths = [".deps/**", "candidate-dependencies/**"]
    if module == "CONTENT":
        dependency_paths += ["packages/soulidity_standard/**", "packages/soulidity_foundation/**",
                             "offline-vendor/**", "frozen-original/**"]
    return {
        "schema_version": "1.0", "module_id": module, "repository": plan["repository"],
        "nature": contract["nature"], "purpose": contract["purpose"],
        "authoritative_state": contract["authoritative_state"], "semantic_units": contract["semantic_units"],
        "source_provenance": sources,
        "artifact_state": {"repository_creation": "not_performed_by_generator",
            "source_migration": "pending", "build": "not_run", "runtime_acceptance": "not_run",
            "independent_deployment": "not_verified", "remote_ci_execution": "not_run"},
        "management": {"functions": ["planning", "organizing", "leading", "controlling"],
            "capabilities": ["module_contract_validation", "existing_record_reference", "evidence_attachment"],
            "role_recommendation": plan["maintenance_role_mapping_recommended"],
            "no_competing_board": True, "preserve_active_owners": True,
            "original_record_registry": registry, "original_scope_references": records,
            "current_record_ref": None, "responsibility_mappings": assignment},
        "write_boundary": {"repository_only": True, "writable_paths": ["**"],
            "owned_semantic_units": contract["semantic_units"], "cross_repository_edits": "forbidden",
            "source_authority_switch": "pending_single_writer_cutover",
            "external_shared_resources": "exclusive_holder_required; worktree does not isolate wallet/deployment/state",
            "non_writable_paths": [".deps/**", "candidate-dependencies/**", "evidence/extraction-original/**"]},
        "engineering_capabilities": {"provided_interfaces_design": contract["provided_interfaces"],
            "selected_dependencies_design": contract["selected_dependencies"],
            "prohibited_dependencies": contract["prohibited_dependencies"],
            "runtime_capabilities_verified": [], "management_role_grants_runtime_authority": False,
            "upgrade_authority_grants_runtime_authority": False},
        "engineering_permissions": permissions,
        "agent_contract": {
            "identity": {"module": module, "role_recommendation": plan["maintenance_role_mapping_recommended"], "actual_identity": None, "status": "pending"},
            "responsibilities": contract["purpose"],
            "write_scope": {"repository": plan["repository"], "paths": ["**"], "cross_repository": "forbidden",
                            "read_only_dependency_paths": dependency_paths},
            "inputs_outputs": {"inputs": ["fixed_candidate", "original_record", "declared_dependencies"], "outputs": ["module_artifact", "verification_evidence", "original_record_attachment"]},
            "tool_identity": {"status": "pending", "actual_accounts": [], "runtime_session": None},
            "permissions": {"source": "bounded_current_task_only", "publish_deploy_sign_spend_external_message": "requires_existing_explicit_authorization", "authority": contract["authority"]},
            "budget": {"status": "pending", "amount": None, "currency": None, "duration": None, "authorization_ref": None},
            "acceptor": assignment["independent_acceptance"],
            "handoff_location": {"original_record_ref": None, "repository_path": "evidence/handoffs/", "status": "pending"},
            "stop_method": {"method": "stop bounded executor, release exclusive resources, preserve original intent/effects, attach handoff to original record", "unattended_runtime": "not_configured"},
        },
        "delivery_attachment": {"original_record_ref": None, "stage": None, "status": "pending",
            "evidence": [], "remaining_exit_criteria": [],
            "stage_exit_criteria": [{"stage": s, "status": "not_verified", "evidence": [], "exit_criteria": e} for s, e in STAGES.items()],
            "handbook": {"version": "1.0", "date": "2026-10-06", "applicable_sections": ["1–4", "5", "9", "12"],
                "conditional_sections": ["6: funds", "7: contracts", "8.3–8.4: Sui/upgrades", "10: operations"],
                "evidence": [], "remaining_checks": ["Add applicability and actual evidence to the original record"],
                "review_template_ref": "agent-management/templates/product-engineering-review.md"}},
        "compatibility": {"consumer_declaration_fields": CONSUMER_FIELDS, "consumers": [],
            "dependency_fields": DEPENDENCY_FIELDS, "dependency_kinds": DEPENDENCY_KINDS, "dependencies": [],
            "change_dimensions": ["type_format_abi", "behavior", "authority_funds", "migration_legacy_entries"],
            "required_combinations": ["baseline/current", "candidate/current", "candidate/candidate"],
            "reverse_combination_when_consumed": True, "verification_evidence": [],
            "unrelated_consumer_forced_releases_target": 0,
            "consumer_freeze_fields": ["source", "dependency_lock", "configuration", "artifact"]},
        "release_units": [], "production_targets": [],
        "ci": {"scope": "maintenance_contract_only", "product_commands": [],
            "product_verification": "not_run", "local_command": ["python3", "scripts/ci.py"]},
        "pipelines": [{"kind": "ci", "configuration": "template", "remote_execution": "not_run"},
                      {"kind": pipeline, "configuration": "readiness_gate_template", "remote_execution": "not_run"}],
        "release_readiness": {"status": "pending", "candidate_identity": None,
            "original_record_ref": None, "build_evidence": [], "test_evidence": [],
            "combination_evidence": [], "independent_acceptance_evidence": [],
            "authorization_ref": None, "recovery_evidence": []},
    }


def documents(config):
    m, repo = config["module_id"], config["repository"]
    role = config["management"]["role_recommendation"]
    return {
        "README.md": f"""# {repo}

{m}: {config['nature']}. {config['purpose']}

Maintenance entry points: [MODULE](MODULE.md), [Agent boundaries](AGENTS.md), [Compatibility](COMPATIBILITY.md), [Operation and recovery](RUNBOOK.md). Machine configuration: [module.json](module.json).

This batch contains maintenance templates. See actual evidence states in module.json for source migration, real builds, runtime acceptance, independent deployment and remote CI execution; all currently await implementation.
Recommended role: {role}; the original Owner remains unchanged. Unconfirmed actual maintainer and independent acceptor mappings remain pending; a role name is neither an account nor an audit qualification.

```sh
python3 scripts/ci.py
python3 scripts/ci.py --product
python3 scripts/ci.py --release-ready
```

Default CI checks the maintenance contract; `--product` refuses to pass when product commands are unregistered. Readiness gates do not deploy or sign.
""",
        "MODULE.md": f"""# {m} maintenance contract

Nature: {config['nature']}. Authoritative state: {config['authoritative_state']}.
Semantic maintenance unit: {', '.join(config['semantic_units'])}.

Only this repository is writable; gate 0 pins exact original source, type origins, function ABI, release units, all UpgradeCaps and consumers in module.json.
An empty release_units means exact package/artifact boundaries are incomplete; repository counts cannot be treated as counts of independent upgrades or deployments.
{config['engineering_capabilities']['prohibited_dependencies']}

Record management functions planning/organizing/leading/controlling, management-tool capabilities and engineering capabilities separately.
Verify four authority categories individually: source maintenance, version release, production deployment and on-chain control; prove upgrade, asset-control and operational authority separately.

Advance work through the original record; stage, status, evidence and exit criteria are separate fields.
Eight stages: {' → '.join(STAGES)}; stage=null in a new template means the original record's current stage has not yet been reviewed.
Record applicable handbook v1.0 sections, evidence and remaining checks on the original Delivery/DEV/BUG; original scope links and Owners come from the original registry. Do not copy historical statuses into current status.

Cutover: save baseline → pin target authoritative candidate → independent verification → pin consumer versions → combination verification → stop dual writing by ending writes at the old location.
Before cutover, the template is not another issuance authority; verify source cutover separately from on-chain writer/issuer cutover.
""",
        "AGENTS.md": f"""# {m} execution boundaries

- Read MODULE.md, COMPATIBILITY.md, RUNBOOK.md and module.json, then the original record and exact candidate; historical statuses are references only.
- The original Owner and record are the responsibility entry point. The recommended role {role} is not an actual account; unconfirmed maintenance/acceptance mappings remain pending.
- Write this module only in this repository's authoritative worktree; do not modify other repositories incidentally through relative paths, symlinks, integration fixes or tool scripts. Hand cross-repository issues to the corresponding maintainer on the original record.
- Only one writer may work on each semantic unit at a time. Parallel work requires scope authorization, capacity within the original WIP, isolated write domains, pinned inputs, independent review capacity and no shared-resource conflicts.
- Do not treat maintenance/upgrade roles as wallet, asset, operation or deployment authority. Follow the original explicit authorization; documentation creates no new signing, spending or external-sending authority.
- The 10 contract fields are in module.json.agent_contract: identity, responsibilities, write_scope, inputs_outputs, tool_identity, permissions, budget, acceptor, handoff_location, stop_method.
- Attach stage, status, evidence, exit criteria and handbook applicability to the original Delivery/DEV/BUG; do not create another task board. Preserve original milestones and active Owners.
- High-risk work requires review by a qualified, independent actual acceptor; role labels and executor self-review must not masquerade as independent approval.
- Keep build/test at not_run when unexecuted; successful template CI does not establish business acceptance, independent release, deployment or external audit.
""",
        "COMPATIBILITY.md": """# Consumed contracts and verification combinations

Register actual consumers and dependencies in module.json.compatibility; an empty list means gate 0 is incomplete and cannot establish zero dependencies.
Configuration declares eight fields per consumer, eight fields per dependency and seven dependency categories, which CI validates.
Fill in the provider's exact interface, actual actions/types, schema/behavior, required effects, authority/state, failure/exit/recovery, version/artifact and verification/migration evidence separately.

Check changes in four dimensions: types/formats/ABI, behavior, authority/funds, and migration/old entry points.
Verify at least baseline/current, candidate/current and candidate/candidate; add reverse combinations when reverse consumption exists.
Pin source, dependency locks, configuration and artifacts; reject floating latest and incorrect hashes. Reverification does not automatically require republication of unrelated consumers.
For unknown passive extensions, the target is 0 forced market publications; fulfill or explicitly reject funds/authorization/supply/transfer/content/exit obligations according to the actually selected contracts.

Register actual packages/SDK artifacts, type origins, exact dependencies and upgrade boundaries individually in release_units; shared UpgradeCaps must disclose the joint upgrade boundary.
Version numbers, directory separation or a compilable ABI do not prove funds/authorization/recovery compatibility.
""",
        "RUNBOOK.md": """# Operation, failure and recovery

1. Pin the candidate source/diff, dependency lock, configuration/artifact hashes, environment/network, relevant packages/objects and consumed consumers on the original record.
2. Run repository CI and registered product commands; save logs and hashes. Unregistered, unexecuted or failed gates must not be rewritten as passed.
3. An independent actual acceptor checks the exact combination and recovery; release-ready checks that materials are complete. Final release follows the original authorization.
4. Authorized executors perform production deployment, upgrade, initialization and signing against the exact target and read back the result. This template does not perform these actions automatically.
5. Record the original intent/digest, effects, paid resources and checkpoints for failures; query the original result first when the outcome is unknown. A readback failure after success does not make the outcome unknown; do not repeat minting/upload/payment.
6. Frontend/SDK can roll back to pinned artifacts; do not assume on-chain state, transfers or upgrades are reversible. Verify each actual action covered by pause/resume and each legitimate exit.
7. Attach the handoff to the original record and retain source candidates/evidence/remaining conditions; release exclusive resources such as wallets, browsers and deployment environments. Stopping an executor does not delete historical assets or paid resources.

Operational responsibility, monitoring sources/windows/thresholds, recovery drills and actual production targets remain pending until implemented; do not claim monitoring is enabled without actual observations.
Tool repositories do not control business operation gates; handle cross-repository failures for the exact affected combination and hand off to the corresponding maintainer.
""",
    }


def workflow(command, title, manual=False):
    trigger = "  workflow_dispatch:" if manual else "  push:\n  pull_request:"
    return f"""name: {title}
on:
{trigger}
permissions:
  contents: read
jobs:
  check:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          persist-credentials: false
      - run: {command}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--module", action="append", choices=list(EXPECTED))
    args = parser.parse_args()
    source = args.source_root.resolve()
    output = args.output.resolve()
    if output == source or source in output.parents:
        parser.error("output must be outside the authoritative design repository")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error("output must be absent or empty; existing files are never overwritten")
    inputs = {k: source / v for k, v in SOURCES.items()}
    missing = [str(p) for p in inputs.values() if not p.is_file()]
    if missing:
        parser.error("missing design inputs: " + ", ".join(missing))
    raw = {k: p.read_bytes() for k, p in inputs.items()}
    plan = json.loads(raw["plan"])
    contracts = json.loads(raw["contracts"])
    scope = json.loads(raw["scope"])
    registry = registry_refs(json.loads(raw["registry"]))
    if {m["id"]: m["repository"] for m in plan["modules"]} != EXPECTED:
        parser.error("delivery plan module/repository identities differ from approved ten repositories")
    source_meta = {k: {"path": SOURCES[k], "sha256": hashlib.sha256(data).hexdigest()} for k, data in raw.items()}
    by_id = {m["id"]: m for m in contracts["modules"]}
    if set(by_id) != set(EXPECTED):
        parser.error("module contracts must contain the approved ten identities")
    if any(by_id[m]["repository"] != repo for m, repo in EXPECTED.items()):
        parser.error("contract repository identities differ from delivery plan")
    configs = [make_config(m, by_id[m["id"]], source_meta, registry, scope)
        for m in plan["modules"] if not args.module or m["id"] in args.module]
    output.mkdir(parents=True, exist_ok=True)
    generated = []
    for config in configs:
        repo = output / config["repository"]
        repo.mkdir()
        (repo / "scripts").mkdir()
        (repo / ".github/workflows").mkdir(parents=True)
        for name, content in documents(config).items():
            (repo / name).write_text(content, encoding="utf-8")
        dump(repo / "module.json", config)
        shutil.copyfile(HERE / "ci.py", repo / "scripts/ci.py")
        (repo / "scripts/ci.py").chmod(0o755)
        (repo / ".github/workflows/ci.yml").write_text(workflow("python3 scripts/ci.py", "Module contract CI"))
        gate = "integration" if config["module_id"] == "INTEGRATION" else "release"
        (repo / f".github/workflows/{gate}-readiness.yml").write_text(workflow(
            "python3 scripts/ci.py --release-ready", f"{gate.title()} readiness; no publication", manual=True))
        generated.append({"module_id": config["module_id"], "repository": config["repository"],
            "files": {str(p.relative_to(repo)): digest(p) for p in sorted(repo.rglob("*")) if p.is_file()}})
    dump(output / "generation-manifest.json", {"schema_version": "1.0", "artifact_kind": "repository_scaffolds",
        "actual_git_or_remote_creation": False, "source_provenance": source_meta,
        "generator_sha256": digest(Path(__file__)), "modules": generated})
    print(json.dumps({"output": str(output), "modules_generated": len(generated),
        "git_or_remote_created": False, "product_runtime_verified": False}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, OSError) as error:
        print(f"generation failed: {error}", file=sys.stderr)
        sys.exit(1)
