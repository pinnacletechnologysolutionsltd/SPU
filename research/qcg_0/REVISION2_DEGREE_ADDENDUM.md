# QCG-0 Revision 2 degree addendum

Date: 2026-10-22. Independent reviewer: `/root/qcg0_fixture_reviewer`. This supplements, and does not modify, `REVISION2_REVIEW_CERTIFICATE.md`, its values or manifest. Disposition remains REVISE. No additional calculation invocation was used; the following is a direct polynomial-degree proof.

**Confirmed additional correction:** §14 calls “PH3 and PH3h (cubic)”. PH3 is cubic, but the specified PH3h has U=1,V=t,h=1+t. Its coordinate hodograph is

x′=(1+t)(1−t²)=1+t−t²−t³,
y′=2t(1+t)=2t+2t².

With zero initial position, integration gives

x=t+t²/2−t³/3−t⁴/4,
y=t²+2t³/3.

The nonzero −t⁴/4 coefficient proves that PH3h has position degree **4**, not 3. A constant translation cannot change this degree. Its signed/actual speed on [0,1] is (1+t)(1+t²), degree 3, and its arc-length polynomial has degree 4.

Minimal correction: label PH3 cubic and PH3h quartic wherever degrees or exact jet requirements are stated. An E0-by-degree jet holding the PH3h position must have order at least **4**; order 3 cannot represent its position exactly. Order 4 refers to the full position polynomial, not merely its degree-3 hodograph. This matters when freezing C2 jet order and its conformance cases.

No author source, original review artifact, other campaign or hardware was changed. This independent confirmation grants no freeze or P0 authorization.
