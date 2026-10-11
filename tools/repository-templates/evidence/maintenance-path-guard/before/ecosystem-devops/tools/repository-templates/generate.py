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
    "Plan": "原卡的用户结果、唯一Owner、实际验收者、正常/失败/恢复及Ready明确",
    "Code": "准确变更、独立审查及相关回归；Implemented不等于Released",
    "Build": "固定工具/依赖/配置，源码及制品摘要；无构建需求说明N/A理由",
    "Test": "准确组合、正常/异常/恢复及适用安全反例，未测项和原旅程结果明确",
    "Release": "适用G3、唯一清单、独立验收、放行责任、原授权及恢复边界",
    "Deploy": "同一候选的准确目标及G4读回；线上原操作待验收不得标完成",
    "Operate": "实际运行责任、适用G5、恢复/对账；成功交易先查询原结果",
    "Monitor": "观测窗口/来源/阈值依据及发现对应原DEV/BUG，未知项明确",
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
            original_owner_rule="沿原卡Owner；建议岗位不替换活动Owner"),
        "independent_acceptance": dict(pending, role_recommendation=contract["review_mapping"],
            qualification_evidence=[], independence_evidence=[],
            original_owner_rule="沿原卡验收责任；高风险由有资格的独立实际验收者复核")}
    permissions = []
    for category in ["source_maintenance", "version_release", "production_deployment", "onchain_control"]:
        applicable = not ((tool and category == "onchain_control") or
            (module == "INTEGRATION" and category == "version_release"))
        permissions.append({"category": category, "applicability": "pending" if applicable else "not_applicable",
            "reason": None if applicable else ("工具仓无业务链上控制" if tool and category == "onchain_control" else "Integration不另设版本发布"),
            "effective_authority_paths": [], "actual_holder": None, "authorization_ref": None, "evidence": []})
    pipeline = "cross_repository_integration" if module == "INTEGRATION" else "version_release"
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
            "external_shared_resources": "exclusive_holder_required; worktree does not isolate wallet/deployment/state"},
        "engineering_capabilities": {"provided_interfaces_design": contract["provided_interfaces"],
            "selected_dependencies_design": contract["selected_dependencies"],
            "prohibited_dependencies": contract["prohibited_dependencies"],
            "runtime_capabilities_verified": [], "management_role_grants_runtime_authority": False,
            "upgrade_authority_grants_runtime_authority": False},
        "engineering_permissions": permissions,
        "agent_contract": {
            "identity": {"module": module, "role_recommendation": plan["maintenance_role_mapping_recommended"], "actual_identity": None, "status": "pending"},
            "responsibilities": contract["purpose"],
            "write_scope": {"repository": plan["repository"], "paths": ["**"], "cross_repository": "forbidden"},
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
                "evidence": [], "remaining_checks": ["原卡补适用性及实际证据"],
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

{m}：{config['nature']}。{config['purpose']}

维护入口：[MODULE](MODULE.md)、[Agent 边界](AGENTS.md)、[兼容](COMPATIBILITY.md)、[运行恢复](RUNBOOK.md)。机器配置：[module.json](module.json)。

本批是维护模板。源码迁移、真实构建、运行验收、独立部署和远端CI运行见 module.json 的实际证据状态，当前均待落实。
推荐岗位 {role}；原 Owner 不变。实际维护人与独立验收人未确认处为 pending，角色名不是账号或审计资格。

```sh
python3 scripts/ci.py
python3 scripts/ci.py --product
python3 scripts/ci.py --release-ready
```

默认CI检查维护契约；产品命令未登记时 `--product` 拒绝通过。准备门禁不部署或签名。
""",
        "MODULE.md": f"""# {m} 维护契约

性质：{config['nature']}。权威状态：{config['authoritative_state']}。
语义维护单元：{'、'.join(config['semantic_units'])}。

仅本仓可写；具体原源码、类型来源、函数ABI、发布单元、全部UpgradeCap与消费者由关口0固定到 module.json。
release_units 为空表示未完成准确包/制品边界，不能把仓数当作独立升级或部署数。
{config['engineering_capabilities']['prohibited_dependencies']}

管理职能 planning/organizing/leading/controlling、管理工具能力和工程能力分别记录。
源码维护、版本发布、生产部署、链上控制四类权限逐项核对；升级权、资产控制、运行权分别证明。

推进使用原卡；stage、status、evidence、exit criteria 独立字段。
八阶段：{' → '.join(STAGES)}；新模板 stage=null 表示尚未复核原卡当前阶段。
手册 v1.0 的适用章节、证据和剩余检查写回原 Delivery/DEV/BUG；原范围链接及Owner来自原注册表，历史状态不复制为当前状态。

切换：保存基线 → 固定目标权威候选 → 独立验证 → 消费者固定版本 → 组合验证 → 旧位置停止双边写。
未切换前模板不是另一发行权威；源码切换与链上writer/issuer切换分别验证。
""",
        "AGENTS.md": f"""# {m} 执行边界

- 阅读 MODULE.md、COMPATIBILITY.md、RUNBOOK.md 和 module.json，再读取原卡及准确候选；历史状态只作引用。
- 原 Owner 和原记录是责任入口。推荐岗位 {role} 不是实际账号；未确认维护/验收映射保持 pending。
- 仅在本仓权威工作树写入本模块；禁止通过相对路径、symlink、集成修复或工具脚本顺手修改其他仓库。跨仓问题交接原卡对应维护者。
- 每语义单元同时只有一个写入者。并行须范围授权、原WIP容纳、写域隔离、输入固定、独立审查容量和共享资源无冲突。
- 禁止把维护/升级角色当钱包、资产、运行、部署权限；沿原明确授权，不从文档产生新签名、支出或外发权限。
- 合同10字段在 module.json.agent_contract：identity、responsibilities、write_scope、inputs_outputs、tool_identity、permissions、budget、acceptor、handoff_location、stop_method。
- 将阶段、状态、证据、退出条件和手册适用性附在原 Delivery/DEV/BUG，不创建另一任务板；原里程碑及活动Owner保留。
- 高风险必须由具备资格且独立的实际验收者复核；角色标签和执行者自审不得冒充独立批准。
- build/test 未执行就保持 not_run；模板CI成功不等于业务验收、独立发布、部署或外部审计。
""",
        "COMPATIBILITY.md": """# 所用契约和验证组合

在 module.json.compatibility 登记真实消费者和依赖；空清单表示尚未完成关口0，不能声称零依赖。
每消费者八字段、每依赖八字段及七种依赖类别由配置声明并由CI校验。
提供方准确接口、实际动作/类型、schema/行为、必要效果、权限/状态、失败/退出/恢复、版本/制品和验证/迁移证据分别填写。

变更检查类型/格式/ABI、行为、权限/资金、迁移/旧入口四维。
至少验证 baseline/current、candidate/current、candidate/candidate；存在反向消费时加反向组合。
固定源码、依赖锁、配置和制品，拒绝浮动 latest 与错误哈希；重验不自动要求重发无关消费者。
未知被动扩展目标为市场被迫发布0；资金/授权/供给/转移/内容/退出义务按实际选用契约执行或明确拒绝。

release_units 中逐个登记真实包/SDK制品、类型来源、精确依赖与升级边界；共用UpgradeCap必须披露共升级边界。
版本号、目录拆分或ABI能编译不证明资金/授权/恢复兼容。
""",
        "RUNBOOK.md": """# 运行、失败和恢复

1. 在原卡固定候选的源码/差异、依赖锁、配置/制品摘要、环境/网络、相关包/对象与所用消费者。
2. 执行本仓CI与已登记产品命令；保存日志和摘要。未登记/未跑/失败的关口不得改写为通过。
3. 由独立实际验收者检查准确组合及恢复；release-ready 检查材料齐备，最终放行仍沿原授权。
4. 生产部署、升级、初始化与签名由已授权执行者在准确目标执行并读回。本模板不自动执行这些操作。
5. 故障记录原意图/digest、effects、已付资源与检查点；未知结果先查原结果。成功后读回失败不改成未知，不重复铸造/上传/付款。
6. 前端/SDK可回退固定制品；链上状态、转账、升级不假设可撤销。暂停/恢复覆盖的实际动作和合法退出逐项核实。
7. 交接附在原记录，保留源候选/证据/剩余条件；释放钱包、浏览器、部署环境等独占资源。停止执行者不删除历史资产或已付资源。

运行责任、监控来源/窗口/阈值、恢复演练及真实生产目标在落实前保持 pending；无真实观测不得宣称监控启用。
工具仓不拥有业务运行门控权；跨仓故障按受影响精确组合处理，交接对应维护者。
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
