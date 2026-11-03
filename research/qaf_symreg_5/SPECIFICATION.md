# SYMREG-5: trusted mathematical contexts

This software-only experiment wraps unchanged SYMREG-4 certificates in a
version-5 envelope. A separately provisioned, trusted in-process authority
allocates monotonically increasing epochs and value identifiers, retains
immutable context revisions, and supplies the checker with its state. A label
may be reused only by explicit request; this creates a fresh epoch. Allocation
is bounded and fails closed rather than wrapping. Persistence and concurrent
authority instances are outside this model.

Each successful register write allocates a new identity. Old values and
premises remain in the context, but the updated binding creates a new revision.
In this prototype, allocating an identity alone is preparation; the new binding
becomes current only when the trusted authority provisions the next revision.
The authority explicitly supplies concrete values, branch declarations and
premises; SYMREG-4 validates premise truth, not the origin of those values or
branch feasibility. An expired epoch never regains current authorization.

The independent checker uses the authority's immutable snapshot, not a
producer-supplied context. It reports mathematical verification, identity
consistency, and current authorization separately. A historical mathematical
proof may still verify after a write or expiry; only the active revision is
authorized. A certificate with no current-register assertion is authorized
only for historical knowledge, never as a current-register assertion.
Certificate context hashes bind exact snapshots; they are not authentication.
The authority view must itself be trusted and consistently provisioned. No
cryptographic authentication, durable anti-rollback storage, ISA execution,
hardware guarantee, or branch-feasibility proof is claimed.

Resource limits: at most 32 epochs, 64 identities per epoch, 128 revisions per
epoch, and the unchanged SYMREG-4 certificate and context limits. Inputs and
outputs use its canonical ASCII JSON. Unrecognized versions, stale revisions,
invalid proofs and exhausted resources fail closed.
