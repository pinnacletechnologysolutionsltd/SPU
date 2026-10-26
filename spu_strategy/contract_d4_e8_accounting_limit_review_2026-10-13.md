# D4/E8 accounting-limit preflight

```bash
python3 -m json.tool build/d4_e8_math_20261013/accounting_limit_preflight_01/lower_bound.json
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_d4_e8_accounting_limit_review_2026-10-13.md docs/D4_E8_ACCOUNTING_LIMIT_PREFLIGHT_2026-10-13.md
```

Date: 2026-10-13. Status: BLOCKED IMPLEMENTATION; proposed correction only.
Qualification HOLD. No campaign command, attempt or execution limit authorized.
This preflight preserves the original comparison contract and all source hashes.
Spec author and halt-and-flag reviewer: same preparer, sequential roles.
Independent reviewer sign-off: PENDING.

## 1. Defect and source clauses

Read the [comparison contract](contract_d4_e8_comparison_readiness_2026-10-13.md)
sections2,4 and6. It requires dense rational matrix multiplication, n additions
per cell starting from zero, normalization on every rational operation, and
no implicit pre-cancellation or zero skipping. Its proposed2,000,000-unit limit
applies per arm per case; shared table setup has a separate limit. Matrix
descriptor construction is case work, not shared static-table setup.

The E8 fixtures include actual word lengths128 and256. The stated schedule has
a conservative arithmetic-only lower bound already above the per-case ceiling.
This is independent of the vector values, matrix coefficients and host speed.
It would force valid-fixture refusals in one representation and prevent a
complete matched comparison under the original proposed profile.

## 2. Lower-bound certificate

Each normalization of a rational (a,d), d>0, must perform at least:

| Primitive work | Minimum units |
|---|---:|
| Denominator zero check and sign check | 2 |
| Two absolute values for Euclid | 2 |
| Euclid zero checks, including termination | 2 |
| At least one Euclid remainder, since the initial denominator is positive | 1 |
| Two Euclid state moves | 2 |
| Two checked quotients: zero check, remainder, remainder-zero check, quotient each | 8 |
| Total per normalization | 17 |

A rational multiply therefore costs at least2+17=19 units. A rational addition
costs at least3+1+17=21 units. Every dense inner-product term requires both,
so costs at least40 units. A word of lengthL in dimensionn costs at least
40*L*n^3 units for matrix composition alone.

For E8, n=8:

* L=128:40*128*512=2,621,440 units.
* L=256:40*256*512=5,242,880 units.

These bounds exclude operand/result type and range checks, reads/writes,
loop controls, allocation/release, normalization validation, input admission,
static setup, conversion, serialization and final materialization. They are
not measured costs or runtime estimates. Actual full modeled costs can be larger.

The bound guarantees that10 of the120 existing cases exceed the proposed limit
on their matrix arm: five E8 forward128 cases and five inverse-pair128 cases.
These are10 cases, not10 new workloads. Other arms and lengths may also exceed
the limit; this certificate does not establish that they fit.

## 3. Minimal proposed correction and implementation sequence

Do not change fixtures, skip normalization, shorten inverse pairs, move
case-specific matrix composition into static setup, or raise a limit silently.
Treat2,000,000 units as an unresolved proposed ceiling, not a ratified limit
that all valid fixtures can satisfy. Preserve the fixed full accounting schedule.

Before qualification, derive a conservative full-work upper bound for each arm
over the120 declared cases and a simultaneous live-storage upper bound. Use
exact operation schedules, maximum token counts and finite scalar widths;
do not execute the full comparison merely to select a favorable limit.
Submit a common ceiling covering the largest bound for independent review.
If that ceiling is unacceptable, submit a separately reviewed smaller fixture
domain and report it as a different comparison. The current120-case identity
must remain unchanged. No particular replacement ceiling is approved here.

Then resume the previously requested isolated adapter, wire-decoder and ledger
implementation, with short literal witnesses. Keep proposed research limits
distinct from CPU hardware limits and separate them from campaign wall time.
Budget changes cannot authorize a campaign. Independent review, source freeze
and separate owner-authorized execution limits remain prerequisites.

## 4. Stop boundary and evidence

The root engineering contract requires: "If a defect is found, HALT immediately
and flag the flaw ... rather than implementing broken logic or silently rewriting
the architecture." Implementation has therefore stopped before changing adapters.
No existing source, fixture, contract, qualified evidence, CPU or RTL was modified.

Evidence: `build/d4_e8_math_20261013/accounting_limit_preflight_01/` contains the
arithmetic certificate, source references and unchanged manifest checks.
The1,048,576-bit storage ceiling remains UNESTABLISHED; this arithmetic bound
does not prove or disprove it. Independent reviewer sign-off remains PENDING.
No540 arm evaluations or120-case campaign ran. Surd CPU backend priority and
the exclusion of all FPGA/board/RTL/ISA work remain unchanged.
