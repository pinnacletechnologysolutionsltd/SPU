"""Immutable packets and strict host-injection validation for the software model."""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Packet:
    kind: int
    source: int
    sequence: int
    payload: int
    target: int | None
    sender: int
    egress: int
    path: tuple

    def key(self):
        return self.kind, self.source, self.sequence, self.sender, self.egress

    def record(self):
        return dict(kind=self.kind, source=self.source, sequence=self.sequence,
                    payload=self.payload, target=self.target, sender=self.sender,
                    egress=self.egress, path=list(self.path))

    def transmitted(self, sender, egress, receiver):
        return replace(self, sender=sender if self.kind else 0,
                       egress=egress if self.kind else 0, path=self.path + (receiver,))


def injections(rows, size):
    if type(rows) not in (list, tuple):
        raise ValueError('INJECTION_CONTAINER')
    schedule, identifiers, ordinals = {}, set(), set()
    for row in rows:
        if type(row) is not dict:
            raise ValueError('INJECTION_ROW')
        kind = row.get('kind', 'unicast')
        if type(kind) is not str or kind not in ('unicast', 'wavefront'):
            raise ValueError('PACKET_KIND')
        fields = {'tick', 'source', 'sequence', 'payload', 'ordinal'}
        fields |= {'target'} if kind == 'unicast' else set()
        if not fields <= row.keys() or not row.keys() <= fields | {'kind'}:
            raise ValueError('INJECTION_FIELDS')
        if any(type(row[k]) is not int for k in fields):
            raise ValueError('INJECTION_INTEGER')
        if any(row[k] < 0 for k in ('tick', 'sequence', 'ordinal')):
            raise ValueError('INJECTION_NONNEGATIVE')
        if not 0 <= row['source'] < size or (kind == 'unicast' and not 0 <= row['target'] < size):
            raise ValueError('INJECTION_ENDPOINT')
        identity = (int(kind == 'wavefront'), row['source'], row['sequence'])
        if identity in identifiers or row['ordinal'] in ordinals:
            raise ValueError('DUPLICATE_INJECTION_ID')
        identifiers.add(identity)
        ordinals.add(row['ordinal'])
        packet = Packet(*identity, row['payload'], row.get('target'),
                        -1 if identity[0] else 0, -1 if identity[0] else 0, (row['source'],))
        schedule.setdefault(row['tick'], []).append((row['ordinal'], packet))
    return {tick: tuple(sorted(items)) for tick, items in schedule.items()}
