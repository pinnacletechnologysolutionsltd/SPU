"""Operation ledger: categories, phases, transactions, event context, retained-state peaks (contract §2/§3)."""
from events import OpBudget, Refusal, event_id

CATS = ("M", "A", "S", "D", "K", "G_calls", "G_bits", "W_bits", "M2")
PEAKS = ("W_peak_raw", "W_peak_red", "T_ret_peak", "L_peak")


def bn(x):   # bit-length of a magnitude, with bn(0) = 1 (contract §2)
    return max(1, abs(x).bit_length())


def _p2(q):  # informational M2: the *value* is a power of two (2, 1/2, 4, 1/16 ...)
    return (q.d == 1 and q.n > 0 and q.n & (q.n - 1) == 0) or (q.n == 1 and q.d & (q.d - 1) == 0)


class Ledger:
    GRAND = [0]          # process-wide counted M, A, S, D, K events (committed and attempted), incremented BEFORE each op
    LIMIT = 1000000      # hard budget (contract §9): the operation that would exceed it is never executed

    def __init__(self, profile, arm):
        self.profile, self.arm = profile, arm
        self.cum = {ph: dict.fromkeys(CATS, 0) for ph in "PQ"}
        self.pk = {ph: dict.fromkeys(PEAKS, 0) for ph in "PQ"}
        self.attempt = dict.fromkeys(CATS, 0)
        self.phase, self.qid, self.step, self.k, self.depth = "P", None, None, 0, 0
        self.c, self.p = dict.fromkeys(CATS, 0), dict.fromkeys(PEAKS, 0)

    # -- transaction: committed ledger vs append-only attempt evidence --
    def begin(self, phase, qid=None):
        self.phase, self.qid = phase, qid
        self.c, self.p = dict.fromkeys(CATS, 0), dict.fromkeys(PEAKS, 0)
        self.step, self.k, self.depth = None, 0, 0

    def commit(self):
        for c in CATS:
            self.cum[self.phase][c] += self.c[c]
        for k in PEAKS:
            self.pk[self.phase][k] = max(self.pk[self.phase][k], self.p[k])

    def rollback(self):
        for c in CATS:
            self.attempt[c] += self.c[c]

    # -- event context: nested primitive calls share the enclosing step's counter --
    def enter(self, label):
        L = self

        class _Ctx:
            def __enter__(s):
                if L.depth == 0:
                    L.step, L.k = label, 0
                L.depth += 1

            def __exit__(s, *exc):
                L.depth -= 1
        return _Ctx()

    def tick(self):
        self.k += 1
        if Ledger.GRAND[0] >= Ledger.LIMIT:
            raise OpBudget(self.event())
        Ledger.GRAND[0] += 1

    def event(self, sub=None):
        return event_id(self.arm, self.phase, self.qid, self.step, self.k, sub)

    def peak(self, key, v):
        self.p[key] = max(self.p[key], v)

    def check(self, value, bound_kind, sub):
        bl = abs(value).bit_length()
        if bound_kind == "raw":
            self.peak("W_peak_raw", bl)
            if bl > self.profile.raw:
                raise Refusal("ARITH_LIMIT", self.event(sub))
        else:
            self.peak("W_peak_red", bl)
            if bl > self.profile.red:
                raise Refusal("ARITH_LIMIT", self.event(sub))

    def retain(self, objs):
        """Observation point: distinct retained rational objects (T_ret_peak)."""
        seen, bits = set(), 0
        for o in objs:
            if id(o) not in seen:
                seen.add(id(o))
                bits += bn(o.n) + bn(o.d) + 1
        self.peak("T_ret_peak", bits)

    def total(self):
        t = {c: self.cum["P"][c] + self.cum["Q"][c] for c in CATS}
        t.update({k: max(self.pk["P"][k], self.pk["Q"][k]) for k in PEAKS})
        return t
