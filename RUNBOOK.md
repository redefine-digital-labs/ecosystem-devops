# Operation, failure and recovery

1. Pin the candidate source/diff, dependency lock, configuration/artifact hashes, environment/network, relevant packages/objects and consumed consumers on the original record.
2. Run repository CI and registered product commands; save logs and hashes. Unregistered, unexecuted or failed gates must not be rewritten as passed.
3. An independent actual acceptor checks the exact combination and recovery; release-ready checks that materials are complete. Final release follows the original authorization.
4. Authorized executors perform production deployment, upgrade, initialization and signing against the exact target and read back the result. This template does not perform these actions automatically.
5. Record the original intent/digest, effects, paid resources and checkpoints for failures; query the original result first when the outcome is unknown. A readback failure after success does not make the outcome unknown; do not repeat minting/upload/payment.
6. Frontend/SDK can roll back to pinned artifacts; do not assume on-chain state, transfers or upgrades are reversible. Verify each actual action covered by pause/resume and each legitimate exit.
7. Attach the handoff to the original record and retain source candidates/evidence/remaining conditions; release exclusive resources such as wallets, browsers and deployment environments. Stopping an executor does not delete historical assets or paid resources.

Operational responsibility, monitoring sources/windows/thresholds, recovery drills and actual production targets remain pending until implemented; do not claim monitoring is enabled without actual observations.
Tool repositories do not control business operation gates; handle cross-repository failures for the exact affected combination and hand off to the corresponding maintainer.
