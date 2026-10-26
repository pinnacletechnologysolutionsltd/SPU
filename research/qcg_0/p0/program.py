"""Step programs: named steps executed in written order, with static liveness for L_peak (contract §2 'L')."""


class Step:
    def __init__(self, label, target, reads, fn):
        self.label, self.target, self.reads, self.fn = label, target, tuple(reads), fn


def _count(v):
    if isinstance(v, dict):
        return sum(_count(x) for x in v.values())
    return len(v) if isinstance(v, (list, tuple)) else 1


def run(steps, env, L, retained=()):
    """Execute `steps` over `env` (dict). A scratch value is live from the step that creates it until the last
    step, in the written order, that reads it; retained names never die. Updates L_peak."""
    last = {}
    for i, s in enumerate(steps):
        for r in s.reads:
            last[r] = i
    live = {}
    for i, s in enumerate(steps):
        with L.enter(s.label):
            val = s.fn(env, L)
        if s.target is not None:
            env[s.target] = val
            if s.target not in retained:
                live[s.target] = _count(val)
        nret = sum(_count(env[n]) for n in retained if n in env)
        L.peak("L_peak", nret + sum(live.values()))
        for r in s.reads:
            if last.get(r) == i and r in live:
                del live[r]
    return env
