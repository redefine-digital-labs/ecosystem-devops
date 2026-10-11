# Source transition actual review — 2026-10-10

Read-only scope: the five repository-extraction helpers, workspace/source-authority metadata, and registered NativeCustody transition. No whole-goal or security certification; no actual Sui, network, source/evidence/metadata mutation, commit, remote, chain, or signing operation.

## Actual snapshot

- Guard and read-only split verification pass:52 original baseline rows,54 unique current production authority files,82 registered current inputs,10 SDK forwarding aliases,10 local Git roots.
- Native transition:5 modified production sources retain their original baseline SHA and match their explicit previous SHA;23 changed inputs total,2 added retained `NATIVE.PRODUCER` source bodies,4 added nonproduction inputs.
- Registered manifest SHA matches the workspace pin: `80ce8d8881af0ecee5c7f148511f3c3252577a46ffe64fb04ea1b45859cac611`.
- Supplementary actual checks pass for17 whole-package frozen inputs,9 partial frozen inputs, and10 SDK frozen inputs: current hashes, recovery hashes, regular recovery files and independent current/recovery paths. Current metadata hashes stayed unchanged during review.
- Ownership JSON remains pre-Native (`derived_production_sources_count=0`); root will regenerate it. This is pending, not a finding.

## Concrete findings

1. **ST-1 / P1 — Whole-package frozen baseline is not checked.** `split_repositories.py:127–135` never inspects `packages[].frozen_before`, and `source_transition_guard.py` checks transition recovery only. A cloned active-package fixture with corrupt source and manifest in the frozen snapshot still passes. Validate every active frozen input against `baseline_inputs`, including regular-file and current-alias checks.
2. **ST-2 / P1 — SDK/partial recovery accepts mutable aliases.** `split_repositories.py:136–155` checks `is_file()` and SHA but accepts a frozen symlink to the current file and `frozen_before` equal to the current file. Four independent temporary fixtures pass incorrectly. Require regular independent recovery inputs for both sections.
3. **ST-3 / P1 — Build accepts drift after its preflight guard.** `build_repository_packages.py:23–25,36–47,52–64` has no full guard after build/test and its commands contain no `--install-dir`. A local fake tool changing registered `Move.toml` or `Move.lock` during build/test yields success evidence; a postbuild guard rejects the actual final inputs. The changed-manifest fixture records a SHA different from the final file. Isolate build output and recheck full current/frozen inputs before successful evidence acceptance. No actual Sui source/lock mutation is asserted by this review.

## Control counts

Existing offline unit controls:23/23 pass. Additional temporary fixture controls:8, comprising1 positive latest-manifest acceptance test that passes and7 adversarial rejection tests that are incorrectly accepted. Total:31 offline controls.

The positive build fixture accepts the explicitly registered latest manifest SHA and leaves original candidate/baseline SHA dictionaries unchanged. The baseline-preservation path is correct; the missing recovery/postbuild rejection paths require repair.

Machine-readable report: `/tmp/source-transition-actual-review-20261010.json`.
