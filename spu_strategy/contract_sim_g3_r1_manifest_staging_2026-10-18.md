# SIM-G3-R1 — Complete SG-0 reference bundle staging

**Date:** 2026-10-18  
**Status:** PREPARED — CAMPAIGN NOT AUTHORIZED  
**Disposition:** Harness repair and focused tests prepared; request separate authorization before replay.  
**Parent:** `contract_sim_g3_sg0_cpp_conformance_2026-10-18`

## 1. Purpose

Complete the SIM-G3 verifier evidence packaging after the first campaign's
read-only verifier rejected its staged SG-0 bundle because the root
`manifest.json` was omitted. The first campaign remains unchanged at
`build/sim_g3/qualification_20261018_01/`; its passing packet/frame outputs and
failed verifier record remain historical evidence. This amendment uses a new
output directory and does not retry the first campaign.

## 2. Narrow harness amendment

`research/sim_g3/__main__.py` now stages the exact root manifest bytes alongside
all members listed by its `files` map. Before creating the staging directory,
the helper checks the pinned manifest digest, exact member-name set, safe
relative paths and every member digest. The read-only verifier checks that the
staged tree contains exactly the manifest-declared members plus the root
`manifest.json`, with no missing or additional files.

`research/sim_g3/test_staging.py` covers:

- Exact root-manifest bytes and the complete declared member set are staged.
- Altered manifest bytes are rejected before destination creation.
- Missing members and substituted member names are rejected before writes.
- Changed member contents are rejected before writes.
- An existing destination is refused and left unchanged.

The prior `test_handoff.py` suite remains unchanged. No SG-0 geometry, expected
packet/frame, schema adapter, SIM-G2A source or executable, renderer, ISA, RTL,
or FPGA flow is changed.

## 3. Prepared source identity and focused evidence

The amended harness must remain byte-identical to these files before any
campaign authorization is used:

| File | SHA-256 |
|---|---|
| `research/sim_g3/__init__.py` | `731be69431a2ab0370efa0b1b2d8fcb51fcbf37c109f3de00fd678bbfd9fa173` |
| `research/sim_g3/handoff.py` | `e68a8c69cac32e26578701c6b59d9bd7edb49ed082f785b0d4d2fc8bc34c0f40` |
| `research/sim_g3/__main__.py` | `d9d0756d10ef30f7488361b27395726c39408eb2257226526fbb3e7c7e3c7cef` |
| `research/sim_g3/test_handoff.py` | `85a0565b0c6e842af66a9d9cf4ece4c3edfa457bd84ac47a3495b08bae041131` |
| `research/sim_g3/test_staging.py` | `6c40edee019f12c572be60468fd4208be153e427e0be65c275bccfb25d686b3e` |
| `research/sim_g3/README.md` | `cd6dade9ee88ef7c059a333667873991af2597c4581880fd070a328fcae1bc47` |

Focused preparation command:

```bash
python3 -m unittest research.sim_g3.test_handoff research.sim_g3.test_staging -v
```

Preparation result: **12/12 PASS**. The focused tests exercise the staging
helper only; they do not run the SIM-G3 replay or claim packet/frame
qualification. `git diff --check` passed for the amended harness and this
contract.

## 4. Proposed one-attempt replay envelope

This is a proposal, not execution authorization.

| Constraint | Proposed limit |
|---|---:|
| Harness implementation | Complete; no further pass in this tranche |
| Replay attempts | One |
| Per-command timeout | 60 seconds |
| Cumulative campaign budget | 300 seconds |
| Automatic retries/extensions | None |
| Existing attempt | Preserve unchanged |
| New evidence directory | `build/sim_g3/qualification_r1_20261018_01/` |
| Source/fixture/renderer changes | Prohibited |

Before execution, verify all six harness source hashes above, confirm the fresh output
path does not exist, and recheck all frozen parent-contract source and fixture
identities. On any mismatch or timeout, stop and preserve partial R1 evidence.
Do not rebuild the SIM-G2A executable or repeat the first campaign's outputs.

Proposed exact commands, each with a 60-second external limit:

```bash
timeout 60s python3 -m research.sim_g3 run --out build/sim_g3/qualification_r1_20261018_01
timeout 60s python3 -m research.sim_g3 verify build/sim_g3/qualification_r1_20261018_01
```

The runner's existing 300-second cumulative deadline also applies. The
qualification output is the fresh R1 evidence directory; the original
qualification directory and its verifier failure are not to be edited.

## 5. Acceptance

R1 may close only if the replay record passes for both frozen scenes, the
read-only verifier passes against the complete staged bundle, all pinned source
and fixture identities match, and the final evidence binds to those identities.
Packet, RGB8 and depth outcomes remain separate; the existing SG-0 depth
differences are retained and no C++ depth-equivalence claim is added.

Any failure leaves SIM-G3 **INCOMPLETE**. No retry, implementation repair or
budget extension is authorized by this prepared contract.
