# QCG-0 independent fixture review — bounded calculation allowance

Date: 2026-10-22. Authority: owner's explicit QCG-0 fixture-review GO in this
conversation, including a requirement to bound fixture-generation calculations
before execution. This record scopes that authorization; it grants no pilot GO.

Independent reviewer: fresh-context /root/qcg0_fixture_reviewer, separate from
the QCG-0 author and HEX-SOM acceptance context. Author scratch calculations
are unavailable and must not be consulted. Codex /root coordinates filing only.

Pinned documents verified before calculations:

    b33205e92370a41de5d1b7806f8435057065ea5272ea21866f5700be99025fa8  research/qcg_0/QCG0_PREREGISTRATION.md
    e64af826a304f9d73095a486e9fc9be75eab61ce42adb64c006b4c429f76e2a9  docs/QSG2_PH_CURVE_SPECIFICATION.md
    f7b876e77ef2b5e1b9ec914d2a4dae9c834058f46aa5fec1c4899863c13529bb  docs/QSG2_SOFTWARE_RESULTS.md
    1f6c5b94ab610f4950a4f2244803aeb17def3adf7a21ea50d5664c2759b98c82  research/qcg_0/QCG0_FIXTURE_REVIEW_PACKET.md

Class A independent mathematical fixture calculations only: fresh exact rational
polynomial/resultant/Bernstein/retiming calculations and verification of literal
reference outputs. No candidate engines, cost benchmarks or QCG-0 P0. No training,
hardware, network from calculation scripts, installation, services or other campaign.
Literature lookup is read-only and separate from calculation process resources.

Local foreground allowance: at most three calculation invocations, each externally
limited to 30 seconds and 1 GiB address space; cumulative external ceiling 90 seconds.
No child processes in calculation scripts. At most 4096 candidate tuples and
10 MiB cumulative review outputs; rational coefficients limited to 4096 reduced
bits and 16384 raw bits. Ordinary correction within these three slots is allowed;
record every invocation and failure. No automatic timeout retry, additional slot,
budget increase or splitting expensive work to evade policy. Stop at exhaustion.

Inspect scripts and verify external executables/callability before calculation.
Use /usr/bin/timeout --signal=KILL 30 /usr/bin/prlimit
--as=1073741824:1073741824 -- /usr/bin/python3 -B -I <review-script>.
Record actual argv, cwd, limits, source/script identities, stdout/stderr, exit and
resource accounting from stdlib where available; /usr/bin/time is not required.

All authored scripts, scratch and artifacts remain within research/qcg_0/;
review-only helper directory review/ may hold disposable scratch and transcripts.
Required final certificate/values paths are those in the supplied review packet.
Refuse overwrite of final certificate/values; preserve intermediate failure logs.
Do not edit pre-registration, review packet, pinned sources or any other campaign.
Do not record hashes in the pre-registration: that remains an author/owner action
after review. A separate review manifest records artifact identities.

Report PASS, REVISE or BLOCKED with exact evidence. Mathematical certification
does not authorize candidate implementation or P0 execution, which remain HOLD.
