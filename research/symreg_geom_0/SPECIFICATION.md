# SYMREG-GEOM-0: certified quadratic-form preservation

Scope: exact vectors in Q(sqrt(3))² with Q(x,y)=x²+y². The independent
version-1 `SYMREG-GEOM` certificate records a sequence of at most 32 2×2
integer matrices and a claimed composition. The producer composes the sequence
and answers the symbolic query without reading vector coefficients. The checker
independently multiplies those matrices in application order, confirms the
claimed result, and verifies MᵀM=I exactly. This matrix identity implies
Q(Mv)=Q(v) for all v over Q(sqrt(3)), by distributivity and commutativity.
Certificates contain no trusted preservation label. Entries are restricted
to -2..2, intermediate products to absolute value at most 1024, and canonical
ASCII JSON to 16 KiB; malformed input or limits are rejected.

A separate concrete check evaluates Q on supplied rational coefficient pairs.
Concrete agreement does not establish a universal invariant. The symbolic
result is conditional on the vector actually being transformed by the matrix;
the certificate does not authenticate vector identity, execution, context,
branch feasibility or freshness. SYMREG-5's restart counterexample remains.
There is no assertion of finite-width ISA, RTL, FPGA, or performance behavior.
