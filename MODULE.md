# DEVOPS maintenance contract

Nature: shared engineering tools. Authoritative state: engineering artifacts and operational evidence only; not a mandatory business runtime point.
Semantic maintenance unit: shared delivery tools.

Only this repository is writable; gate 0 pins exact original source, type origins, function ABI, release units, all UpgradeCaps and consumers in module.json.
An empty release_units means exact package/artifact boundaries are incomplete; repository counts cannot be treated as counts of independent upgrades or deployments.
['runtime business path']

Record management functions planning/organizing/leading/controlling, management-tool capabilities and engineering capabilities separately.
Verify four authority categories individually: source maintenance, version release, production deployment and on-chain control; prove upgrade, asset-control and operational authority separately.

Advance work through the original record; stage, status, evidence and exit criteria are separate fields.
Eight stages: Plan → Code → Build → Test → Release → Deploy → Operate → Monitor; stage=null in a new template means the original record's current stage has not yet been reviewed.
Record applicable handbook v1.0 sections, evidence and remaining checks on the original Delivery/DEV/BUG; original scope links and Owners come from the original registry. Do not copy historical statuses into current status.

Cutover: save baseline → pin target authoritative candidate → independent verification → pin consumer versions → combination verification → stop dual writing by ending writes at the old location.
Before cutover, the template is not another issuance authority; verify source cutover separately from on-chain writer/issuer cutover.
