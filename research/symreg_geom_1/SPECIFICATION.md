# SYMREG-GEOM-1 — symmetric quadratic forms

For v=(x,y) over Q(sqrt(3)), use Q_G(v)=vᵀGv for any symmetric 2×2
integer matrix G with entries -3..3, including indefinite and degenerate
forms. A versioned certificate carries G, up to 32 integer transformations
with entries -4..4, and their claimed composition M in application order.
The independent checker recomputes M and every entry of MᵀGM and compares
it to G. Intermediate matrix entries are limited to absolute value 4096 and
canonical ASCII JSON to 16 KiB. Inputs outside these limits are rejected.

For accepted certificates, the matrix identity implies Q_G(Mv)=Q_G(v) for
all v in the domain; it does not depend on numerical vector inputs. A form may
be indefinite or degenerate, so no distance or positive-definiteness claim is
implied. Exact concrete arithmetic provides independent finite examples.
Certificates do not authenticate context, establish actual execution or fix
SYMREG-5's restart replay. No ISA, RTL or physical claim is made.
