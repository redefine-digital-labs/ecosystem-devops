# Consumed contracts and verification combinations

Register actual consumers and dependencies in module.json.compatibility; an empty list means gate 0 is incomplete and cannot establish zero dependencies.
Configuration declares eight fields per consumer, eight fields per dependency and seven dependency categories, which CI validates.
Fill in the provider's exact interface, actual actions/types, schema/behavior, required effects, authority/state, failure/exit/recovery, version/artifact and verification/migration evidence separately.

Check changes in four dimensions: types/formats/ABI, behavior, authority/funds, and migration/old entry points.
Verify at least baseline/current, candidate/current and candidate/candidate; add reverse combinations when reverse consumption exists.
Pin source, dependency locks, configuration and artifacts; reject floating latest and incorrect hashes. Reverification does not automatically require republication of unrelated consumers.
For unknown passive extensions, the target is 0 forced market publications; fulfill or explicitly reject funds/authorization/supply/transfer/content/exit obligations according to the actually selected contracts.

Register actual packages/SDK artifacts, type origins, exact dependencies and upgrade boundaries individually in release_units; shared UpgradeCaps must disclose the joint upgrade boundary.
Version numbers, directory separation or a compilable ABI do not prove funds/authorization/recovery compatibility.
