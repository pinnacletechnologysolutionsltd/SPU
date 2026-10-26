"""Arm base: preparation (phase P), requests (phase Q) as atomic transactions, retained-state snapshots."""
from events import Invalid, Refusal, result
from ledger import Q
from program import Step, run


def steps(rows):
    return [Step(*r) for r in rows]


class Arm:
    """`p_rows` / `q_rows(self)` give step tuples; `retained` names stay in `state`; subclasses set `flag_name`."""
    name = "?"
    retained = ()
    evolving = ()          # retained names a request may replace (assigned only after the request succeeds)

    def __init__(self, profile, source):
        from account import Ledger
        self.L = Ledger(profile, self.name)
        self.source, self.state, self.prep = source, None, None

    # -- phase P --
    def import_source(self, env):
        L = self.L
        for key, pairs in self.source.items():
            env[key] = [Q.imp(n, d, L, "%s.%d" % (key, i)) for i, (n, d) in enumerate(pairs)]

    def prepare(self):
        L = self.L
        L.begin("P")
        env = {}
        try:
            self.import_source(env)
            run(steps(self.p_rows()), env, L, self.retained)
            self.state = {k: env[k] for k in self.retained if k in env}
            L.retain(self.retained_objects(self.state))
            L.commit()
            self.prep = None
        except (Refusal, Invalid) as e:
            L.rollback()
            self.state, self.prep = None, (e.code, e.event)
        return self.prep

    def extra_env(self, env, L):
        pass

    def retained_objects(self, state):
        out = []
        for v in state.values():
            out += list(v) if isinstance(v, (list, tuple)) else [v]
        return out

    # -- phase Q: one atomic request --
    def request(self, qid, tpair, req="BUNDLE"):
        L = self.L
        if self.state is None:
            return result("NOT_APPLICABLE", None, None) if self.prep is None else result("REFUSED", self.prep[0], self.prep[1])
        L.begin("Q", qid)
        try:
            env = dict(self.state)
            env["t"] = Q.imp(tpair[0], tpair[1], L, "t")
            self.extra_env(env, L)
            run(steps(self.q_rows(req)), env, L, self.retained)
            out = self.outputs(env)
            for n in self.evolving:
                if n in env and self.state.get(n) is not env[n]:
                    self.state[n] = env[n]
            L.retain(self.retained_objects(self.state))
            L.commit()
            return result("OK", None, None, out)
        except Refusal as e:
            L.rollback()
            return result("REFUSED", e.code, e.event)
        except Invalid as e:
            L.rollback()
            return result("INVALID", e.code, e.event)

    def snapshot(self):
        return {k: (list(v) if isinstance(v, list) else v) for k, v in self.state.items()}

    def restore(self, snap):
        self.state = {k: (list(v) if isinstance(v, list) else v) for k, v in snap.items()}
