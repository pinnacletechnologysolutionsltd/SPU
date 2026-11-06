# SOUL-MEM-2 authorized implementation contract

The full proposed contract and the owner's 2026-11-06 implementation
authorization are in the conversation. This document records the four binding
clarifications accepted before registration:

1. Complete canonical serialized decision state is budgeted after every atomic
   update. Empty state too large gives `INFEASIBLE_BUDGET`; no hidden state.
2. Retention and eviction are deterministic and registered. An M2 index must
   agree with the retained archive; losses and failures are recorded.
3. A separately coded bounded checker evaluates cited propositions and registered
   direct/transitive rules as SUPPORTED, UNSUPPORTED or UNKNOWN. This is support
   under supplied observations and rules, not outside-world truth.
4. Calibration uses separate data; budgets, source, scenarios, policies and
   scoring are hashed before registered runs. Repairs to registered results
   require distinct attempt identities and preservation of earlier results.

The owner authorizes bounded software implementation, focused tests, controls
and two registered runs, then stop. Prior experiments and consolidation are
unchanged. No production integration, publication, push, SPU/QAF change,
transformer, autonomous agent or hardware work is authorized. Equal budgets
are not equal retained information.
