# SSM consolidation and evidence preservation

Date: 2026-10-18
Status: owner requested preservation, architecture consolidation and interface design
Roles: current agent specifies, prepares artifacts and audits; no delegation.

## Scope and commands

1. Preserve SSM-3's qualified original source overlay, ten proof artifacts,
   replay verifier, exact campaign evidence and dependency records under the
   Class A rules in `docs/BUILD_ARTIFACT_RETENTION.md`. No original deletion.
2. Create `research/ssm3_baseline_20261018/` as a local compact package/index.
   Reuse RET-1 package/restore/verify APIs unchanged. Use a fresh staging/restore
   child at `build/repository_cleanup/ssm3_preservation_20261018_01/`.
3. Restore independently from the package after staging becomes unavailable;
   replay ten original proofs, regenerate exact bytes and run 14 focused methods
   with restored-only imports. Verify tree parity afterward. Cap foreground
   reproduction at 55 seconds; no full repository qualification campaign.
4. Create `docs/SSM_ARCHITECTURE_2026-10-18.md` and
   `docs/SOM_SYMBOLIC_INTERFACE_DESIGN_2026-10-18.md`. Update only navigation and
   the SSM-3 retention disposition in `docs/README.md` and
   `docs/BUILD_ARTIFACT_RETENTION.md`.
5. Execute the new user-facing demo, proof-check, checksum and restore-verifier
   commands. Run `python3 tools/doc_audit.py --actual-pass 238` and
   `git diff --check -- docs/README.md docs/BUILD_ARTIFACT_RETENTION.md docs/SSM_ARCHITECTURE_2026-10-18.md docs/SOM_SYMBOLIC_INTERFACE_DESIGN_2026-10-18.md research/ssm3_baseline_20261018 spu_strategy/contract_ssm_consolidation_2026-10-18.md`.

## Limits, provenance and acceptance

Do not change SSM-0–3, their predecessor APIs or historical source manifests.
No SSM-4, SOM bridge implementation/training, GPU, simulator, ISA or RTL change.
No new generic retention tooling or archive-format implementation.

The package is a self-contained scoped research overlay, not a complete Git or
full regression restoration. It includes the original pinned source archive,
original launch metadata and current ancillary licenses/restoration helpers.
Record the source archive's normalized-mode limitation, external runtime tools,
exact package digests and manifest, restore commands, tool identities and report.

External archive location remains unselected and zero independent storage copies
are established. Local package/restore copies share a failure domain. Record
Class A preservation and incomplete archive graduation honestly; retain every
original. No deletion, pruning review approval, commit or tag is authorized.

Restoration result: PASS_FOCUSED_RESTORATION; ten proofs replayed and reproduced,
14 focused tests passed, entry/exit restored tree parity checked. Python import
path/module audit is not an OS sandbox. The original 244-test qualification is
historical evidence, not rerun during this consolidation.

The SOM design permits adaptive candidate ordering only as a proposal. Exact
validation and proof replay remain authoritative relative to fixed original
inputs. New inferred relationships without certificates remain hypotheses.
Implementation, fitting, evaluation split and budgets need a separate contract.

Halt on package/pin mismatch, restored modules outside the restored root, proof
byte mismatch or a retention claim exceeding the supported restoration scope.


## Scope steering received during consolidation

Owner requested the sequence consolidation -> SG-0 -> SSM-4 -> SOM–SSM.
Add `docs/SG0_SYMBOLIC_GPU_INTERFACE_DESIGN_2026-10-18.md` and
`docs/SSM4_CERTIFIED_GEOMETRIC_STATE_DESIGN_2026-10-18.md` as design-only artifacts.
Inspect current T1d APIs, check candidate affine/projected vertices with existing
functions and document the fixed allowlist boundary for workbench visibility.
Do not implement SG-0 or SSM-4 in this preparation tranche. SSM-4 design begins
now; implementation requires a frozen/reviewed SG-0 interface and a separate
contract. No dependence on all SIM-G2A/Router-F1 work finishing is introduced.
