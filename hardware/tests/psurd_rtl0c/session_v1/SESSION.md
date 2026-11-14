# RTL-0C session package v1: every step in order

Generated listing of `script.json` for review. Payloads are hex; a `.rec` file is a 213-byte expected record.
A STATUS payload is: flags (bit 0 image-valid, bit 1 load-open, bit 2 record-valid), run state, cause or FF, run id (4 bytes, little-endian).

| # | Phase | Step | Command | Expected status | Expected payload |
|---|---|---|---|---|---|
| 0 | P2 | first STATUS | status  | OK | 0000ff00000000 |
| 1 | P2 | RESULT before any run | result  | REFUSED | 0a |
| 2 | P2 | START with no image | start budget 5 | REFUSED | 08 |
| 3 | P3 | load program 1 | load prog1.spui | OK | — |
| 4 | P3 | STATUS after load | status  | OK | 0100ff00000000 |
| 5 | P4 | START program 1 | start budget 1,000 | OK | — |
| 6 | P4 | wait program 1 | wait  | OK, no run in flight |  |
| 7 | P4 | RESULT program 1 | result  | OK | record_00_b4c72302a881.rec |
| 8 | P4 | STATUS after run | status  | OK | 05030001000000 |
| 9 | P5 | load A-A | load A-A.spui | OK | — |
| 10 | P5 | START A-A | start budget 10,000 | OK | — |
| 11 | P5 | wait A-A | wait  | OK, no run in flight |  |
| 12 | P5 | RESULT A-A | result  | OK | record_01_4150ac7bbcbc.rec |
| 13 | P5 | load A-B | load A-B.spui | OK | — |
| 14 | P5 | START A-B | start budget 10,000 | OK | — |
| 15 | P5 | wait A-B | wait  | OK, no run in flight |  |
| 16 | P5 | RESULT A-B | result  | OK | record_02_b8fb66523373.rec |
| 17 | P5 | load A-C | load A-C.spui | OK | — |
| 18 | P5 | START A-C | start budget 10,000 | OK | — |
| 19 | P5 | wait A-C | wait  | OK, no run in flight |  |
| 20 | P5 | RESULT A-C | result  | OK | record_03_8973b1add388.rec |
| 21 | P5 | load A-D | load A-D.spui | OK | — |
| 22 | P5 | START A-D | start budget 10,000 | OK | — |
| 23 | P5 | wait A-D | wait  | OK, no run in flight |  |
| 24 | P5 | RESULT A-D | result  | OK | record_04_e64deab3235a.rec |
| 25 | P5 | load A-E | load A-E.spui | OK | — |
| 26 | P5 | START A-E | start budget 10,000 | OK | — |
| 27 | P5 | wait A-E | wait  | OK, no run in flight |  |
| 28 | P5 | RESULT A-E | result  | OK | record_05_a880d79f354e.rec |
| 29 | P5 | load A-F | load A-F.spui | OK | — |
| 30 | P5 | START A-F | start budget 10,000 | OK | — |
| 31 | P5 | wait A-F | wait  | OK, no run in flight |  |
| 32 | P5 | RESULT A-F | result  | OK | record_06_10d92651dd59.rec |
| 33 | P5 | load B_K33 | load B_K33.spui | OK | — |
| 34 | P5 | START B_K33 | start budget 10,000 | OK | — |
| 35 | P5 | wait B_K33 | wait  | OK, no run in flight |  |
| 36 | P5 | RESULT B_K33 | result  | OK | record_07_56c4de4af123.rec |
| 37 | P5 | load B_K34 | load B_K34.spui | OK | — |
| 38 | P5 | START B_K34 | start budget 10,000 | OK | — |
| 39 | P5 | wait B_K34 | wait  | OK, no run in flight |  |
| 40 | P5 | RESULT B_K34 | result  | OK | record_08_856aa241facc.rec |
| 41 | P6 | load A-A for repetition | load A-A.spui | OK | — |
| 42 | P6 | repeat 1: START | start budget 10,000 | OK | — |
| 43 | P6 | repeat 1: wait | wait  | OK, no run in flight |  |
| 44 | P6 | repeat 1: RESULT | result  | OK | record_01_4150ac7bbcbc.rec |
| 45 | P6 | repeat 1: STATUS | status  | OK | 0503000a000000 |
| 46 | P6 | repeat 2: START | start budget 10,000 | OK | — |
| 47 | P6 | repeat 2: wait | wait  | OK, no run in flight |  |
| 48 | P6 | repeat 2: RESULT | result  | OK | record_01_4150ac7bbcbc.rec |
| 49 | P6 | repeat 2: STATUS | status  | OK | 0503000b000000 |
| 50 | P6 | repeat 3: START | start budget 10,000 | OK | — |
| 51 | P6 | repeat 3: wait | wait  | OK, no run in flight |  |
| 52 | P6 | repeat 3: RESULT | result  | OK | record_01_4150ac7bbcbc.rec |
| 53 | P6 | repeat 3: STATUS | status  | OK | 0503000c000000 |
| 54 | P6 | repeat 4: START | start budget 10,000 | OK | — |
| 55 | P6 | repeat 4: wait | wait  | OK, no run in flight |  |
| 56 | P6 | repeat 4: RESULT | result  | OK | record_01_4150ac7bbcbc.rec |
| 57 | P6 | repeat 4: STATUS | status  | OK | 0503000d000000 |
| 58 | P6 | repeat 5: START | start budget 10,000 | OK | — |
| 59 | P6 | repeat 5: wait | wait  | OK, no run in flight |  |
| 60 | P6 | repeat 5: RESULT | result  | OK | record_01_4150ac7bbcbc.rec |
| 61 | P6 | repeat 5: STATUS | status  | OK | 0503000e000000 |
| 62 | P6 | load prog1_again | load prog1_again.spui | OK | — |
| 63 | P6 | START prog1_again | start budget 1,000 | OK | — |
| 64 | P6 | wait prog1_again | wait  | OK, no run in flight |  |
| 65 | P6 | RESULT prog1_again | result  | OK | record_00_b4c72302a881.rec |
| 66 | P7 | image with a wrong CRC | load bad_crc.spui | REFUSED | 04 |
| 67 | P7 | STATUS: image invalid, record kept | status  | OK | 0403000f000000 |
| 68 | P7 | START refused: no image | start budget 5 | REFUSED | 08 |
| 69 | P7 | earlier record still readable | result  | OK | record_00_b4c72302a881.rec |
| 70 | P7 | header with revision 0x02 | load_begin  | REFUSED | 02 |
| 71 | P7 | reload program 1 | load prog1.spui | OK | — |
| 72 | P7 | START with B = 0 | start budget 0 | REFUSED | 09 |
| 73 | P7 | record unchanged after refused START | result  | OK | record_00_b4c72302a881.rec |
| 74 | P7 | load the long-running loop | load loop.spui | OK | — |
| 75 | P7 | START long run | start budget 17,000,000 | OK | — |
| 76 | P7 | STATUS during the run: RUNNING | status  | OK | 0101ff10000000 |
| 77 | P7 | START during the run: BUSY | start budget 5 | BUSY | — |
| 78 | P7 | LOAD_BEGIN during the run: BUSY | load_begin  | BUSY | — |
| 79 | P7 | RESULT during the run: BUSY | result  | BUSY | — |
| 80 | P7 | STATUS still RUNNING (the run outlasted the commands) | status  | OK | 0101ff10000000 |
| 81 | P7 | wait long run | wait  | OK, no run in flight |  |
| 82 | P7 | RESULT long run: BUDGET record | result  | OK | record_09_98300288fee7.rec |
| 83 | P7 | frame with a bad checksum: BAD_FRAME | raw raw a502050000b2 | BAD_FRAME | — |
| 84 | P7 | STATUS after BAD_FRAME | status  | OK | 05030610000000 |
| 85 | P7 | truncated frame: TIMEOUT | raw raw a5020404000000 | TIMEOUT | — |
| 86 | P7 | STATUS after TIMEOUT | status  | OK | 05030610000000 |
| 87 | P8 | operator: press KEY0 once | pause  | (operator) |  |
| 88 | P8 | STATUS after reset | status  | OK | 0000ff00000000 |
| 89 | P8 | RESULT after reset | result  | REFUSED | 0a |
| 90 | P8 | START after reset | start budget 5 | REFUSED | 08 |
| 91 | P8 | reload program 1 after reset | load prog1.spui | OK | — |
| 92 | P8 | START program 1 after reset | start budget 1,000 | OK | — |
| 93 | P8 | wait after reset | wait  | OK, no run in flight |  |
| 94 | P8 | RESULT equals the P4 record | result  | OK | record_00_b4c72302a881.rec |
