# ecosystem-devops

DEVOPS: shared engineering tools. Pinned-version builds, workflows, artifacts and operational tools.

Maintenance entry points: [MODULE](MODULE.md), [Agent boundaries](AGENTS.md), [compatibility](COMPATIBILITY.md), [operation and recovery](RUNBOOK.md). Machine configuration: [module.json](module.json).

Actual construction: repository extraction, source ownership, build tools and template tools have moved here; old script paths locate the same source. See module.json for detailed evidence statuses; independent deployment and remote CI remain unaccepted.
Recommended role HARBOR; original Owner unchanged. Unconfirmed actual maintainer and independent acceptor mappings remain pending; role names are not accounts or audit qualifications.

```sh
python3 scripts/ci.py
python3 scripts/ci.py --product
python3 scripts/ci.py --release-ready
```

Default CI checks the maintenance contract; `--product` refuses to pass when no product command is registered. Readiness gates do not deploy or sign.

Actual source reconstruction preserves the initial hashes of the original 52 production sources. Changes use `workspace.json`
`source_transitions` references frozen change manifests: each current input, previous hash, recovery copy
and current hash; new implementation sources separately list their sole writer and original duty. `source_transition_guard.py`
verifies continuous transitions, recovery files, current inputs and new source ownership, preventing rewritten baselines from hiding changes.
52 offline controls passed (10 positive, 42 refusals); evidence is in `tools/repository-extraction/evidence/source-transition-guard/`.
Recovery aliases, missed whole-package recovery checks and post-build input drift found by independent review are fixed: whole-package, per-source and SDK recovery copies must be independent and complete; symlinks and same-file/hardlinks cannot masquerade as recovery copies. Builds and tests use separate output directories, then frozen inputs are rechecked; changes retain failure evidence and are refused.
Activation also requires exact packages/paths/current inputs and successful overall verification; previously failed evidence cannot be reused even after files are restored. Input read/location errors must enter the failure record. Actual Model passes a build with isolated outputs; its standalone test count 0 is not business coverage.
This check verifies input integrity; behavior, authority and release acceptance still require actual builds and tests.

## Current checkpoint

See [construction status](CONSTRUCTION_STATUS.md) for current evidence, blockers, recovery material and remote coordination. This checkpoint is not a release.
