"""Experimental byte protocol/state machine, not a production interface.

Frame: b'IV', version=1, opcode, epoch:u16 LE, length:u8, payload, CRC16 LE.
CRC-CCITT initial 0xffff covers header and payload. Exactly two primitives.
BEGIN=1 payload(profile=1,count=2); TRI=2 payload(id:u8,colour:u16,12*i8);
PREPARE=3 and COMMIT=4 empty. Preparation takes three abstract ticks, not
predicted FPGA cycles. A boundary samples queued state before that tick.
"""
import binascii
import struct
from .ivm_frontier_model import Meter, Scene, Triangle, prepare_scene, prepare_triangle


def packet(op, epoch, payload=b''):
    body = b'IV'+struct.pack('<BBHB',1,op,epoch,len(payload))+payload
    return body+struct.pack('<H',binascii.crc_hqx(body,0xffff))


def tri_packet(epoch, t):
    return packet(2,epoch,struct.pack('<BH12b',t.ident,t.colour,
                                    *(v for q in t.vertices for v in q)))


class Receiver:
    def __init__(self, unsafe_commit=False):
        self.active = None
        self.buffer = bytearray()
        self.pending = None
        self.phase = 'IDLE'
        self.queued = None
        self.prepared = []
        self.events = []
        self.meter = Meter()
        self.unsafe_commit = unsafe_commit

    def reject(self, reason, abort=False):
        self.events.append(('REJECT',reason))
        if abort:
            self.pending, self.queued, self.phase = None,None,'IDLE'
            self.prepared = []

    def expire(self):
        if self.buffer or self.phase in ('RECEIVE','PREPARING'):
            self.buffer.clear()
            self.reject('timeout',True)

    def reset(self):
        self.__init__(self.unsafe_commit)  # defined blank; flush all old work

    def feed(self, data):
        for byte in data:
            self.buffer.append(byte)
            if len(self.buffer) >= 2 and self.buffer[:2] != b'IV':
                del self.buffer[0]
                continue
            if len(self.buffer) < 7:
                continue
            length = self.buffer[6]
            if length > 15:
                self.buffer.clear()
                self.reject('length',True)
                continue
            if len(self.buffer) < length+9:
                continue
            raw = bytes(self.buffer)
            self.buffer.clear()
            if binascii.crc_hqx(raw[:-2],0xffff) != int.from_bytes(raw[-2:],'little'):
                self.reject('crc',True)
                continue
            version,op,epoch,_ = struct.unpack('<BBHB',raw[2:7])
            if version != 1:
                self.reject('version',True)
                continue
            self.command(op,epoch,raw[7:-2])

    def command(self, op, epoch, payload):
        if op == 1:
            if self.phase != 'IDLE':
                return self.reject('busy')
            if payload != b'\x01\x02' or epoch == 0 or (self.active and epoch <= self.active.epoch):
                return self.reject('profile/count/epoch')
            self.pending = (epoch,{})
            self.phase = 'RECEIVE'
        elif not self.pending or epoch != self.pending[0]:
            return self.reject('epoch')
        elif op == 2 and self.phase == 'RECEIVE':
            if len(payload) != 15:
                return self.reject('triangle length',True)
            ident,colour,*coords = struct.unpack('<BH12b',payload)
            if ident not in (0,1) or ident in self.pending[1]:
                return self.reject('id/duplicate',True)
            q = tuple(tuple(coords[i:i+4]) for i in range(0,12,4))
            if colour > 4095 or any(sum(v) != 0 or any(abs(c)>9 for c in v) for v in q):
                return self.reject('coordinate/colour',True)
            self.pending[1][ident] = Triangle(ident,colour,q)
        elif op == 3 and self.phase == 'RECEIVE' and not payload:
            if len(self.pending[1]) != 2:
                return self.reject('incomplete')
            self.prepared = []
            self.phase = 'PREPARING'
        elif op == 4 and not payload:
            if self.phase != 'READY':
                if self.unsafe_commit and self.phase == 'PREPARING' and self.active and self.prepared:
                    self.queued = Scene(epoch,(self.prepared[0],self.active.triangles[1]),
                                        self.active.order_field,self.active.order_epoch)
                    self.phase = 'QUEUED'
                else:
                    return self.reject('not ready')
            else:
                self.phase = 'QUEUED'
        else:
            return self.reject('opcode/state')
        self.events.append(('ACCEPT',op,epoch))

    def tick(self, boundary=False):
        if boundary and self.phase == 'QUEUED':
            self.active = self.queued
            self.events.append(('ACTIVATED',self.active.epoch))
            self.pending,self.queued,self.phase = None,None,'IDLE'
            self.prepared = []
        if self.phase == 'PREPARING':
            try:
                epoch,raw = self.pending
                if len(self.prepared) < 2:
                    self.prepared.append(prepare_triangle(raw[len(self.prepared)],epoch,self.meter))
                else:
                    self.queued = prepare_scene(self.prepared,epoch,self.meter)
                    self.phase = 'READY'
                    self.events.append(('READY',epoch))
            except ValueError as e:
                self.reject(str(e),True)
        return self.active  # immutable snapshot token for this frame
