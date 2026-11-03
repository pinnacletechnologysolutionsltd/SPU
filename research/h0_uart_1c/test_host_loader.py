import importlib.util
from pathlib import Path
import struct
import unittest
spec=importlib.util.spec_from_file_location('host_loader',Path(__file__).with_name('host_loader.py'))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

class FakePort:
 def __init__(self):self.pending=b'';self.commands=[]
 def write(self,packet):
  assert h.xor(packet)==0
  cmd=packet[2];payload=packet[4:-1];assert len(payload)==packet[3]
  self.commands.append((cmd,payload))
  body=bytes((0xa5,1,cmd|0x80,0))
  data=(bytes((5,))+struct.pack('<I',7)) if cmd==4 else struct.pack('<6I',13,0,4,0,9,0) if cmd==5 else b''
  body+=bytes((len(data),))+data;self.pending=body+bytes((h.xor(body),));return len(packet)
 def read(self,n):result=self.pending[:n];self.pending=self.pending[n:];return result

class HostTests(unittest.TestCase):
 def test_program_loading_and_result(self):
  w=[0x7000000000000100,0x7000010000000000,0x7000020000000200,0x7000030000000000,0x7000040000000300,0x7000050000000000,0x7100000000000000,0x7300000000000000]+[0x7200000000000000+(i<<40) for i in range(6)]
  port=FakePort();run,result=h.execute(port,w,2)
  self.assertEqual((run,result),(7,(13,0,4,0,9,0)))
  self.assertEqual(port.commands[0],(1,bytes.fromhex('c736e5fd')))
  self.assertEqual(len([x for x in port.commands if x[0]==1]),15)
 def test_short_response_is_uncertain(self):
  port=FakePort();port.read=lambda n:b''
  with self.assertRaisesRegex(TimeoutError,'uncertain'):h.request(port,4)
if __name__=='__main__':unittest.main()
