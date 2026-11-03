"""Bounded, explicitly trusted context provisioner, separate from inference."""
from copy import deepcopy
from research.qaf_symreg_4.checker import DOMAIN, canonical, check_context

MAX_EPOCHS, MAX_IDENTITIES, MAX_REVISIONS = 32, 64, 128


class Authority:
    def __init__(self, name):
        if not isinstance(name, str) or not name or len(name) > 32:
            raise ValueError("authority name")
        self.name = name
        self.epochs = {}
        self.labels = set()
        self.registry = {}
        self.issued = {}
        self.next_identity = 0
        self.active = None

    def allocate(self, label, reuse=False):
        if type(label) is not str or not label or len(label) > 32:
            raise ValueError("label")
        if label in self.labels and reuse is not True:
            raise ValueError("label reused without authorization")
        if len(self.epochs) >= MAX_EPOCHS:
            raise ValueError("epoch limit")
        if self.active is not None:
            self.epochs[str(self.active)]["expired"] = True
        epoch = len(self.epochs) + 1
        self.epochs[str(epoch)] = {"label": label, "expired": False, "snapshots": {}}
        self.labels.add(label)
        self.issued[epoch] = 0
        self.active = epoch
        return epoch

    def identity(self, a, b, requested=None):
        if self.active is None:
            raise ValueError("no active context")
        if self.issued[self.active] >= MAX_IDENTITIES:
            raise ValueError("identity limit")
        if type(a) is not int or type(b) is not int or any(not -(1 << 63) <= n < (1 << 63) for n in (a, b)):
            raise ValueError("coefficient")
        name = "v" + str(self.next_identity)
        if requested is not None and requested != name:
            raise ValueError("identity collision or out-of-order request")
        self.next_identity += 1
        self.issued[self.active] += 1
        self.registry[name] = [a, b]
        return name

    def provision(self, values, branches):
        if self.active is None:
            raise ValueError("no active context")
        record = self.epochs[str(self.active)]
        if len(record["snapshots"]) >= MAX_REVISIONS:
            raise ValueError("revision limit")
        if any(v not in self.registry for v in values):
            raise ValueError("unknown identity")
        context = {"version": 1, "domain": DOMAIN, "scope": "epoch_" + str(self.active),
                   "values": {v: self.registry[v][:] for v in values}, "branches": deepcopy(branches)}
        check_context(context)
        revision = len(record["snapshots"]) + 1
        record["snapshots"][str(revision)] = context
        return revision, canonical(context)

    def expire(self):
        if self.active is None:
            raise ValueError("no active context")
        self.epochs[str(self.active)]["expired"] = True
        self.active = None

    def view(self):
        return canonical({"version": 5, "authority": self.name, "active": self.active,
                          "epochs": deepcopy(self.epochs), "registry": deepcopy(self.registry)})
