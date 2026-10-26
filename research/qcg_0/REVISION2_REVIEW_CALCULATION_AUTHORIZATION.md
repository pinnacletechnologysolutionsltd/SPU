# QCG-0 Revision 2 consistency and additional-fixture review allowance

Date: 2026-10-22. Owner instruction: independent re-inspection and derivation of
new section 9.2 chain, join and closure values in the same pass. Review only;
no freeze, candidate implementation or P0 execution authorization.

Reviewer: /root/qcg0_fixture_reviewer, continuing the independent QCG-0 review,
separate from the author and HEX-SOM acceptance reviewer. Author scratch remains
unavailable. The original review authorization and all certified artifacts are
preserved unchanged; this new task is not a retry or extension of a pilot.

Before starting, recheck all owner-supplied full SHA-256 identities, plus the
unchanged original review packet. Coordinator independently verified the seven
owner-supplied identities on disk, including Revision 2 preregistration hash
fbaf2b5a85615bf6a3ade33c759f2d496596aeff234dcf2ce684f0f25bec4f42.

Class A allowance for this new review: at most two local foreground mathematical
calculation invocations, each externally limited to 30 seconds and 1 GiB
per-process address space; cumulative external ceiling 60 seconds, no children,
network, devices, installations or services. At most 10 MiB cumulative new review
outputs, reduced coefficients at most 4096 bits and raw temporaries 16384 bits.
Ordinary correction within those two slots is allowed and recorded; no automatic
timeout retries, extra slots or increased bounds. Stop at exhaustion.

Use verified callable absolute executables: /usr/bin/timeout --signal=KILL 30
/usr/bin/prlimit --as=1073741824:1073741824 -- /usr/bin/python3 -B -I <review-script>.
Inspect scripts first. Preserve argv/cwd, source and script hashes, transcript,
exit/terminal disposition and stdlib resource accounting. No /usr/bin/time needed.

Derive new section 9.2 expectations independently with exact rational algebra.
Read existing certified values rather than regenerate/reselect the quintic.
Reconcile Cell A conventions and hand counts mathematically, not by benchmarking
candidate engines. Record discrepancies without modifying input documents.

All writes stay in research/qcg_0/. Use new revision-specific scripts, transcripts,
certificate, value JSON and manifest; refuse overwrite. Never edit original
certificate/values/manifest/authorization, pre-registration, packet, diff or
re-review request. No other campaign, source, hardware, RTL or simulator changes.
Report PASS / REVISE / BLOCKED, complete exact outputs and hashes. A mathematical
review PASS would not freeze the experiment or authorize P0.
