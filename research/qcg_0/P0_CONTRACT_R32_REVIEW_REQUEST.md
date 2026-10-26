# QCG-0 P0 contract Revision 3.2: request for independent read-only review

Date: 2026-10-23. From: the QCG-0 author. Read-only inspection; no calculation requested or authorized; the stage allowance remains
ungranted. Subject: `QCG0_P0_EXECUTION_CONTRACT.md` Revision 3.2 (hash in the cover message) and its diff against Revision 3.1
(`2829a167…ee44`, reviewed REVISE). Check only the four corrections and the two stale-text removals, then re-confirm the frozen checklist items
the Revision 3.1 review passed:
* B1: C2's tape-specific steps (S1 c3, c4, c6a; S2 c3, c4, c5, c6b, c12–c14; S3 c1–c5, c6, c7–c15), the narrower read projections, and that excluded jets are neither shifted nor read.
* B2: FDINIT with t_0 = 0, the triangular traversal and the single `FDINIT.<poly>` counter; FDSTEP's ascending-j rule; the route-context rule for event ids.
* B3: the runner cap contract and the launcher's OUTPUT_CAP attribution (status 90, 153, `CAP_BREACH`, near-limit leaf), and that COMPLETE is impossible after any of them.
* B4: the single finalization path (no `set -e`, 4 KiB reserve, bounded metadata, post-run pin check always attempted, exactly one marker, `FINALIZE_FAILED`).
Report PASS / REVISE / BLOCKED. A PASS does not authorize freeze, implementation, execution or the stage allowance.
