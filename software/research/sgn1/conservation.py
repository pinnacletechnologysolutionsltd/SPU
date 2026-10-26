"""Per-identity conservation and independent integer-payload accounting."""
from collections import Counter


def identity(packet):
    return packet['kind'], packet['source'], packet['sequence']


class Accounting:
    def __init__(self, rows, adjacency):
        self.rows, self.adjacency = rows, adjacency
        self.labels = {(int(r.get('kind', 'unicast') == 'wavefront'), r['source'], r['sequence']): r
                       for r in rows}
        if len(self.labels) != len(rows):
            raise AssertionError(('DUPLICATE_INPUT_ID',))
        self.injected, self.delivered = Counter(), Counter()
        self.created, self.first, self.suppressed = Counter(), Counter(), Counter()
        self.sums = [0] * len(adjacency)

    def validate_packet(self, packet):
        fields = {'kind', 'source', 'sequence', 'payload', 'target', 'sender', 'egress', 'path'}
        if type(packet) is not dict or not fields <= packet.keys():
            raise AssertionError(('UNVERIFIED', 'packet fields'))
        if (any(type(packet[k]) is not int for k in fields - {'target', 'path'})
                or packet['kind'] not in (0, 1)
                or (packet['target'] is not None and type(packet['target']) is not int)
                or type(packet['path']) is not list or any(type(i) is not int for i in packet['path'])):
            raise AssertionError(('PACKET_CONTENT', packet))
        key = identity(packet)
        row = self.labels.get(key)
        if row is None or packet['payload'] != row['payload'] or packet['target'] != row.get('target'):
            raise AssertionError(('PACKET_CONTENT', packet))
        return key

    def admit(self, tick):
        for row in self.rows:
            if row['tick'] == tick:
                key = int(row.get('kind', 'unicast') == 'wavefront'), row['source'], row['sequence']
                self.injected[key] += 1

    def consume(self, node_id, event):
        if event['packet'] is None:
            return
        key = self.validate_packet(event['packet'])
        action = event['service']
        if action == 'LOCAL_DELIVERY':
            self.delivered[key] += 1
            if self.delivered[key] != 1:
                raise AssertionError(('DUPLICATE_DELIVERY', key, node_id))
            self.sums[node_id] += self.labels[key]['payload']
        elif action == 'FIRST_VISIT':
            self.first[key] += 1
            self.created[key] += len(self.adjacency[node_id])
            self.sums[node_id] += self.labels[key]['payload']
        elif action == 'DUPLICATE_SUPPRESSION':
            self.suppressed[key] += 1

    def boundary(self, states, flights):
        inventory = Counter()
        for state in states:
            for packet in state['inbox']:
                inventory[self.validate_packet(packet)] += 1
            for task in state['pending']:
                key = self.validate_packet(task['packet'])
                if key[0] != 1:
                    raise AssertionError(('FANOUT_PACKET_CLASS', key))
                inventory[key] += 1
        for flight in flights:
            inventory[self.validate_packet(flight['packet'])] += 1
        for key in self.labels:
            left = self.injected[key] + (self.created[key] if key[0] else 0)
            right = inventory[key] + (self.first[key] + self.suppressed[key] if key[0] else self.delivered[key])
            if left != right:
                raise AssertionError(('CONSERVATION', key, left, right))
        actual = [state['accumulator'] for state in states]
        if actual != self.sums:
            raise AssertionError(('APPLICATION_SUM', actual, self.sums))

    def final(self):
        expected = [0] * len(self.adjacency)
        for key, row in self.labels.items():
            if self.injected[key] != 1:
                raise AssertionError(('UNADMITTED_INPUT', key))
            if not key[0]:
                expected[row['target']] += row['payload']
                if self.delivered[key] != 1:
                    raise AssertionError(('MISSING_DELIVERY', key))
            else:
                seen, pending = {row['source']}, [row['source']]
                while pending:
                    for neighbour in self.adjacency[pending.pop()]:
                        if neighbour not in seen:
                            seen.add(neighbour)
                            pending.append(neighbour)
                for node in seen:
                    expected[node] += row['payload']
                if self.first[key] != len(seen):
                    raise AssertionError(('WAVEFRONT_COVERAGE', key, self.first[key], len(seen)))
        if self.sums != expected:
            raise AssertionError(('FINAL_SUM', self.sums, expected))
