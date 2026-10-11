# Source transition fix recheck — 2026-10-10

Read-only bounded review of the five repository-extraction helpers against `before-review-fix` and the initial ST-1/ST-2/ST-3 report. Repository/source/metadata/CURRENT remained unchanged by this review; all new fixture/report writes were under `/tmp`. No actual Sui, network, chain, commit, remote or signing operation.

## Result

- **ST-1 resolved:** common guard checks every active-package frozen baseline input and its independence. The prior corrupt frozen source/manifest fixture rejects; the added missing/symlink/samefile/hardlink controls pass.
- **ST-2 resolved:** partial and client recovery use the same regular/independent copy check. All four prior alias fixtures reject. SDK10 current inputs now enter expected hashes before transition overlay.
- **ST-3 partially resolved:** isolated install directories and postbuild/posttest checks reject the original drift fixtures with failure evidence. The activation consumer still accepts a failed integrity record after current bytes are recovered.

## Remaining concrete findings

1. **P1 / ST-3-acceptance — Failed integrity evidence can activate a package.** `split_repositories.py:164–166` checks only build/test return codes and candidate hashes. A fake test changes `Move.lock`, returns0, and the builder exits1 while recording `exit_code=0`, `test_exit_code=0`, nonempty `input_errors_after_test`, and a workspace evidence pointer. Restoring the lock to the expected baseline lets `activate` accept the same failed record, move the old package and create its forwarding locator; final verification succeeds. Require an explicit overall integrity/success result and reject either post-tool error list. Add this restored-input acceptance regression.
2. **P2 / ST-3-exception — Guard exceptions lose structured failure evidence.** A fake build/test replaces a registered production source with a self-symlink. `source_transition_guard.py:113` raises `RuntimeError` from `Path.resolve`; uncaught guard calls at `build_repository_packages.py:46/55` abort before `evidence.json` and the workspace pointer at `68–70`. Both stage fixtures exit1 and preserve raw logs, but no structured failure record. Convert canonicalization/filesystem failures to diagnostics or preserve failed evidence in an exception handler. No unsafe success was observed for this exception case.

## Verification

- Existing offline controls **43/43 PASS**.
- Original temporary repro controls **8/8 PASS**: one latest-manifest positive, seven prior rejection cases.
- Actual common guard **92 inputs**, **52 original +2 derived production sources**, **10 SDK inputs**, **10 local Git roots**: PASS.
- Read-only `split.verify` passed with `put` intercepted in memory. Regenerated source-authority map includes52 original/2 derived sources.
- The1 downstream acceptance control fails its required rejection; the2 exception controls fail structured-evidence preservation.
- Five tool files and workspace/source-authority metadata hashes stayed unchanged during the reviewed checks.

Handbook v1.0 (2026-10-06), §§1–5,9,12 applies to this scoped Code/Build/Test review. Full release/security/CI deployment, independent upgrade authority and product acceptance remain outside scope. Current milestone handoff at `/Users/naoer/.codex/worktrees/soul-dof-v1-rebuild/soulidity/docs/codex/handoffs/20261010-native-custody-sdk-source-increment.md` was read and preserved; primary CURRENT intentionally remains unchanged.

Machine-readable evidence: `/tmp/source-transition-fix-recheck-20261010.json`. Repro scripts: `/tmp/source-transition-fix-recheck-20261010.py`, `/tmp/source-transition-exception-capture-20261010.py`.

This initial partial report is historical for its exact reviewed hashes; the root began a further patch after checks. Final recheck is pending.
