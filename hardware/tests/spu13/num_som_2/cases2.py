"""NUM-SOM-2 BMU cases: the 19 immutable NUM-SOM-1 cases, 11 numerical-boundary cases, 3 legacy large-key witnesses."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "num_som_1"))
from cases import CASES as BASE  # noqa: E402


def four(p, q):
    return [(p, q)] * 4


BOUNDARY = [("B_+9457,+9457", four(9457, 9457)), ("B_-9457,+9457", four(-9457, 9457)),
            ("B_+9457,-9457", four(9457, -9457)), ("B_-9457,-9457", four(-9457, -9457)),
            ("B_+9458,+9458", four(9458, 9458)), ("B_-9458,+9458", four(-9458, 9458)),
            ("B_+9459,+9459", four(9459, 9459)), ("B_-9459,+9459", four(-9459, 9459)),
            ("B_+9500,+9500", four(9500, 9500)), ("B_-9500,+9500", four(-9500, 9500)),
            ("B_mixed", [(9457, -9457), (-9457, 9457), (9457, 9457), (-9457, -9457)])]
BIG = [("BIG_A46341", [(46341, 0), (0, 0), (0, 0), (0, 0)]),
       ("BIG_A46340", [(46340, 0), (0, 0), (0, 0), (0, 0)]),
       ("BIG_A-46341", [(-46341, 0), (0, 0), (0, 0), (0, 0)])]
CASES = BASE + BOUNDARY + BIG
