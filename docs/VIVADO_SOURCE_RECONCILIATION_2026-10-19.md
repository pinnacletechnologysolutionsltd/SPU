# Vivado source reconciliation and dependency disposition

Date: 2026-10-19. Status: read-only reconciliation complete; no FPGA tools run.
No production file, historical evidence, installed tool or licence was changed.
The owner reviewed this record as static reconciliation PASS and selected C1
as the prospective identity. The [environment readiness note](VIVADO_ENVIRONMENT_READINESS_2026-10-19.md)
keeps installation/licensing and vendor elaboration ahead of any routing decision.

## Source identities and comparison selection

The [initial preparation](VIVADO_REFERENCE_PREPARATION_2026-10-19.md) captured
current sources but compared their hashes with an older source guard. The
single core mismatch is now explained and preserved as a full unified diff.

| Identity | spu13_core.v SHA-256 | Permitted interpretation |
|---|---|---|
| H0: historical reference | `cd831bc4648b13344c670596b824856505a38cb15e6a603b0ab6b8e983e1da4a` | Historical open-flow evidence; not the current RTL |
| C1: current prospective baseline | `2f860c315ef757f0620d30c7ffcfbdb8c57545da3a7c1c9450f5c2efdc518036` | Proposed source pin for a future independent implementation |

Captured C1 agrees byte-for-byte with the current working sources at audit.
The H0 core was recovered from the preserved `implementation_freeze_01`
snapshot, without changing the working tree. All 35 H0 inputs match the old
`build_repair_freeze_03/sources.sha256` guard. H0 and C1 differ only in the core
within this captured dependency set.

The core diff contains two substantive changes:

1. Byte lane indexing `% 13` is replaced with the bounded `qr_lane` helper,
   using 19 compare/subtract steps. For an unsigned byte, at most 19
   subtractions are mathematically sufficient. This source inspection is not
   a new RTL equivalence or timing qualification result.
2. HEX read-port sequencing adds a `hex_active` cycle before projection and
   completion, allowing the accepted source address to reach the read port.
   This changes sequencing; do not presume cycle equivalence with H0.

H0 contains runtime modulo syntax prohibited by today's RTL contract. Preserve
it as immutable historical evidence; do not restore it into production or
silently choose it for a new synthesis campaign. C1 is the recommended future
comparison identity. A controlled same-source flow comparison requires a
preserved open-flow artifact demonstrably generated from C1, or a separately
authorized paired implementation. H0's results alone cannot supply that match.
Selecting C1 here authorizes neither paired run nor architecture changes.

## Dependency audit

The initial 33-file inventory omitted two source-relative includes:

- `hardware/rtl/core/spu13/fpga_chain_arith.vh`
- `hardware/rtl/core/spu13/spu13_regen_arith.vh`

Both are now copied and hashed in the reconciliation packets. Static recursion
finds four include edges, no unresolved literal includes and no active-text
`$readmemh`/`$readmemb` calls within the selected source/include set. The core's
MEM_FILE parameter belongs to its disabled sequencer configuration; this is
not evidence that every alternate core configuration is memory-independent.
The inventory conservatively retains the previously captured arch memory files.

The 35-file packet provides complete literal-include closure for the 19
selected RTL files. The saved Yosys log establishes the historical selected
module hierarchy, including Surd execution/arithmetic, REGEN, chain, QRF/ECC
and initialization. The core diff introduces no new module instantiations.
This establishes the static source inventory and historical hierarchy evidence;
Vivado-specific elaboration closure is still NOT VERIFIED. Without running a
vendor elaborator, do not claim that unknown primitive, macro, include-search
or language interpretation issues have been eliminated.

A later project must explicitly include both `hardware/rtl/arch` and
`hardware/rtl/core/spu13` as include search directories, use the captured input
root as its working directory, and refuse external source fallbacks. The old
33-file Tcl recipe remains preserved and is superseded as a complete-input
proposal. No replacement implementation flow is executed by this audit.

## Historical artifact identity and outcome

The audit pins hashes of `integrated_build_04/cpu_1.json`, synthesis script/log,
source guard/list, DSP allocation and detached result. Its terminal marker is
TIMEOUT, exit 124 after 3,600 seconds: an infrastructure outcome, not a failed
mathematical test or a completed route. A mapped JSON exists, but existence
does not imply routed timing success. Later open-backend campaigns retain
their own separate source and evidence identities.

The historical Yosys flow's REGEN soft-multiply policy remains material. Vivado
may infer a different DSP allocation. Even with matched RTL, compare complete
synthesis/placement/routing flows before attributing a difference solely to
the router. Preserve the 25 MHz clock, wrapper and enabled configuration.

## Reproducible audit artifacts

Under `build/vivado_reference/reconciliation_01/`:

- `audit.py` performs only file reads, hashing, textual analysis and report copies.
- `report.json` records include edges, drift, historical artifacts and hierarchy.
- `core_H0_to_C1.patch` preserves the precise core change.
- `H0_historical_evidence_only/` and `C1_current_prospective/` contain separate
  35-file input trees and source manifests.

The audit ran once with `python3 build/vivado_reference/reconciliation_01/audit.py`.
It refuses an existing report. No synthesis, elaboration, placement, routing,
simulation, installation or board access was performed. Installation and a
source-matched, separately approved implementation budget remain future decisions.
