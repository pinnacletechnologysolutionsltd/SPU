"""QROT-1 reproduction data: scenarios and expected QR0 immediately after the QROT step."""

EXPECT_NONADD = 1228  # deterministic LCG vectors in qrot1_repro.py; not a mathematical constant
Z = ((0, 0),) * 4
ROTS = "ROT R0\n"
TAG = "LD R1, 0,0\nLD R2, 0,0\nLD R3, 0,0\nQLOAD QR0, R0\nQROT QR0\n"
SCEN = [  # (name, program, expected QR0 immediately after the QROT step)
    ("e1 x1", "QLDI QR0, 1,0,0,0\nQROT QR0\n", ((2, 1), (0, 0), (0, 0), (0, 0))),
    ("e1 x3", "QLDI QR0, 1,0,0,0\n" + "QROT QR0\n" * 3, ((26, 15), (0, 0), (0, 0), (0, 0))),
    ("FIELD-0 (3,1,0,0)", "QLDI QR0, 3,1,0,0\nQROT QR0\n", ((6, 3), (2, 1), (0, 0), (0, 0))),
    ("signed (-3,5,-7,2)", "QLDI QR0, -3,5,-7,2\nQROT QR0\n", ((8, 4), (24, 12), (0, 0), (18, 9))),
    ("zero", "QLDI QR0, 0,0,0,0\nQROT QR0\n", Z),
    ("all equal (7,7,7,7)", "QLDI QR0, 7,7,7,7\nQROT QR0\n", Z),
    ("gauge (1,2,3,4)", "QLDI QR0, 1,2,3,4\nQROT QR0\n", ((0, 0), (2, 1), (4, 2), (6, 3))),
    ("gauge (5,6,7,8)", "QLDI QR0, 5,6,7,8\nQROT QR0\n", ((0, 0), (2, 1), (4, 2), (6, 3))),
    ("tag r^0", "LD R0, 1,0\n" + TAG, ((2, 1), (0, 0), (0, 0), (0, 0))),
    ("tag r^3", "LD R0, 1,0\n" + ROTS * 3 + TAG, ((97, 56), (0, 0), (0, 0), (0, 0))),
    ("tag r^6", "LD R0, 1,0\n" + ROTS * 6 + TAG, ((5042, 2911), (0, 0), (0, 0), (0, 0))),
    ("tag r^7 wraps", "LD R0, 1,0\n" + ROTS * 7 + TAG, ((1, 0), (0, 0), (0, 0), (0, 0))),
    ("mixed tags r^7,r^0", "LD R0, 1,0\n" + ROTS * 7 + "LD R1, 1,0\nLD R2, 0,0\nLD R3, 0,0\nQLOAD QR0, R0\nQROT QR0\n",
     ((1, 0), (2, 1), (0, 0), (0, 0))),
    ("untagged (5,3)", "LD R0, 5,3\n" + TAG, ((19, 11), (0, 0), (0, 0), (0, 0))),
    ("second operand ignored", "QLDI QR0, 1,0,0,0\nQROT QR0, R5\n", ((2, 1), (0, 0), (0, 0), (0, 0))),
]
