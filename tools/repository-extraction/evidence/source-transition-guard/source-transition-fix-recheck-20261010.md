# Source transition fix recheck — 2026-10-10

**PASS for the bounded offline tooling scope. No remaining concrete findings in the reviewed fixes.**

The five repository-extraction helpers were reviewed against `before-review-fix`, `before-activation-fix` and the original ST-1/ST-2/ST-3 report. All reviewer fixture/report writes remained under `/tmp`; actual source, workspace metadata, evidence, and CURRENT were read-only. No actual Sui, network, chain, commit, remote or signing operation was performed by this review.

## Findings resolved

- **ST-1:** active whole-package frozen baselines are checked against original input hashes, and recovery files must be regular and independent. The prior corrupt source/manifest fixture rejects; existing missing/symlink/samefile/hardlink controls pass.
- **ST-2:** partial and client recovery use the same regular/independent copy check. All four prior mutable-alias fixtures reject. SDK10 current inputs enter expected hashes before transition overlay.
- **ST-3:** build and test use separate install directories and recheck the common guard afterward. Explicit overall `verification_exit_code` distinguishes integrity failure from compiler/test exit codes. Activation requires overall success, empty integrity-error arrays, exact package/path, and current expected inputs. Original drift fixtures reject while preserving structured failure evidence.
- **Follow-up acceptance P1:** recovering input bytes after a failed build/test no longer makes its failure evidence eligible for activation; independent fixture rejects before moving the original package.
- **Follow-up exception P2:** build/test self-symlink mutations now become guard diagnostics and preserve structured failure evidence plus the workspace pointer.
- **Follow-up two-package regression P1:** the baseline-digest variable no longer overwrites the expected-input map. Two successful prepared packages activate and verify in the independent temporary fixture.

## Verified results

- Existing offline suite: **52/52 PASS** (10 positive,42 negative).
- Supplemental temporary runs: **12/12 PASS** — 8 original repro cases,1 failed-evidence activation case,2 exception cases,1 two-package positive case. These overlap the suite’s scenarios and are reported separately.
- Actual common guard: **92 inputs**, **52 original +2 derived production sources**, **10 SDK inputs** — PASS.
- Actual read-only `split.verify`: **10 local Git roots**,52 original/2 derived sources,10 client inputs — PASS. Its `put` was intercepted in memory.
- Regenerated source-authority map records52 original and2 derived sources. The five helper files and workspace/source-authority hashes stayed unchanged during final checks; exact reviewed hashes are in the JSON.

## Scope and continuity

Handbook v1.0 (2026-10-06), §§1–5,9,12 applies to this scoped Code/Build/Test review. Full security, deployed CI/immutable runtime pins, independent upgrade authority and product/release/deploy acceptance remain unverified here. The root’s separate actual Model build is not asserted as behavior verification after the final status patch.

The current native-custody-sdk-source-increment handoff and primary CURRENT were preserved. Historical intermediate reports retain the findings and exact earlier hashes rather than being replaced with success claims.

Final machine-readable evidence: `/tmp/source-transition-fix-recheck-20261010.json`. Historical initial partial report: `/tmp/source-transition-fix-recheck-20261010-initial-partial.{md,json}`. The51-control intermediate JSON and pre-fix two-package reproduction remain under `/tmp`.
