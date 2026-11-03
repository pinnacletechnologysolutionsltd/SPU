#!/usr/bin/env python3
"""Independent exact arithmetic on observed sequencer words and board results."""
from fractions import Fraction
from itertools import product
from math import lcm
from pathlib import Path
import re
import sys

words={"A":{},"B":{}};results={}
for line in Path(sys.argv[1]).read_text().splitlines():
 m=re.fullmatch(r"PROGRAM ([AB]) (\d+) ([0-9a-fA-F]{16})",line)
 if m:
  label,index,value=m[1],int(m[2]),int(m[3],16)
  if index in words[label]:raise ValueError("duplicate word")
  words[label][index]=value
 m=re.fullmatch(r"BOARD_RESULT ([AB]) ([0-9a-fA-F]{48})",line)
 if m:results[m[1]]=int(m[2],16)
for label in ("A","B"):
 if set(words[label])!=set(range(14)) or label not in results:raise ValueError("incomplete trace")
 w=[words[label][i] for i in range(14)]
 for i in range(6):
  if w[i]>>40 != 0x700000+i or w[i]&0xff:raise ValueError("SLI encoding")
 if w[6:8]!=[0x7100000000000000,0x7300000000000000] or w[8:]!=[0x7200000000000000 | (i<<40) for i in range(6)]:raise ValueError("program shape")
 s=[(x>>8)&0xffffffff for x in w[:6]]
 a,b,d=(s[0]|s[1]<<32,s[2]|s[3]<<32,s[4]|s[5]<<32)
 if not d or a >= 1<<63 or b >= 1<<63:raise ValueError("fixture outside oracle scope")
 x=(Fraction(a,d),Fraction(b,d));y=[Fraction(0),Fraction(0)]
 for i,j in product(range(2),repeat=2):y[(i+j)%2]+=x[i]*x[j]*(3 if i+j==2 else 1)
 denominator=lcm(*(v.denominator for v in y)); vals=[int(v*denominator) for v in y]+[denominator]
 expect=tuple(y for x in vals for y in (x&0xffffffff,x>>32))
 actual=tuple((results[label]>>(32*i))&0xffffffff for i in range(6))
 if actual!=expect:raise AssertionError((label,expect,actual))
 print(label,"inputs",(a,b,d),"six slices",expect,"PASS")
print("BOARD_ORACLE PASS")
