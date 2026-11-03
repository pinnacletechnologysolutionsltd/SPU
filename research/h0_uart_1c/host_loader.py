#!/usr/bin/env python3
"""Experimental stop-and-wait v1 loader; pyserial is required for hardware use."""
import argparse
import struct
import time
import zlib

SOF=0xA5

def xor(data):
 value=0
 for byte in data:value ^= byte
 return value

def frame(cmd,payload=b''):
 if not 1 <= cmd <= 5 or len(payload)>9:raise ValueError('invalid request')
 body=bytes((SOF,1,cmd,len(payload)))+payload
 return body+bytes((xor(body),))

def receive(port, cmd):
 header=port.read(5)
 if len(header)!=5:raise TimeoutError('incomplete response; transaction outcome is uncertain')
 if header[:3]!=bytes((SOF,1,cmd|0x80)) or header[4]>24:raise ValueError('invalid response header')
 rest=port.read(header[4]+1)
 if len(rest)!=header[4]+1:raise TimeoutError('incomplete response; transaction outcome is uncertain')
 if xor(header+rest)!=0:raise ValueError('response checksum')
 if header[3]:raise RuntimeError(f'H0 refusal/fault status 0x{header[3]:02x}')
 return rest[:-1]

def request(port,cmd,payload=b''):
 packet=frame(cmd,payload)
 if port.write(packet)!=len(packet):raise IOError('partial UART write; transaction outcome is uncertain')
 return receive(port,cmd)

def execute(port, words, timeout):
 if len(words)!=14 or any(not 0<=x<2**64 for x in words):raise ValueError('14 unsigned 64-bit words required')
 crc=zlib.crc32(b''.join(w.to_bytes(8,'big') for w in words))
 request(port,1,struct.pack('<I',crc))
 for addr,w in enumerate(words):request(port,1,bytes((addr,))+struct.pack('<Q',w))
 request(port,2);request(port,3)
 end=time.monotonic()+timeout
 observed_run=None
 while time.monotonic()<end:
  status=request(port,4)
  if len(status)!=5:raise ValueError('invalid STATUS length')
  flags=status[0];run_id=int.from_bytes(status[1:],'little')
  if observed_run is None:observed_run=run_id
  elif run_id!=observed_run:raise RuntimeError('run identity changed; result ownership uncertain')
  if flags&8:raise RuntimeError('execution fault')
  if flags&4:
   payload=request(port,5)
   if len(payload)!=24:raise ValueError('invalid RESULT length')
   final=request(port,4)
   if len(final)!=5 or int.from_bytes(final[1:],'little')!=run_id or not final[0]&4:raise RuntimeError('result ownership changed')
   return run_id,struct.unpack('<6I',payload)
  time.sleep(0.01)
 raise TimeoutError('execution outcome uncertain; do not assume cancellation')

def main():
 p=argparse.ArgumentParser();p.add_argument('port');p.add_argument('program',help='text file, one hexadecimal instruction per line');p.add_argument('--baud',type=int,default=115200);p.add_argument('--timeout',type=float,default=10)
 a=p.parse_args(); words=[int(line.strip(),16) for line in open(a.program,encoding='utf-8') if line.strip() and not line.lstrip().startswith('#')]
 import serial
 with serial.Serial(a.port,a.baud,timeout=a.timeout,write_timeout=a.timeout) as port:
  run_id,result=execute(port,words,a.timeout);print('run',run_id,'slices',result)
if __name__=='__main__':main()
