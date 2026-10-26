"""Preparation-only catalogue contract vectors; does not publish any assets."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
FIELDS = ("id", "path", "sha256", "group")


def encode(catalogue):
    return (json.dumps(catalogue, indent=2, separators=(",", ": "),
                       sort_keys=False) + "\n").encode("utf-8")


class CatalogueContractTests(unittest.TestCase):
    def setUp(self):
        self.inputs = json.loads((ROOT / "inputs.json").read_bytes())
        self.base_bytes = (ROOT / "catalogue_before.json").read_bytes()
        self.base = json.loads(self.base_bytes)

    def test_existing_serialization_is_preserved(self):
        self.assertEqual(encode(self.base), self.base_bytes)
        self.assertEqual(len(self.base["scenes"]), 11)
        self.assertEqual(hashlib.sha256(self.base_bytes).hexdigest(),
                         self.inputs["catalogue_before_sha256"])
        for entry in self.base["scenes"]:
            self.assertEqual(tuple(entry), FIELDS)

    def test_new_entry_input_order_cannot_change_catalogue_bytes(self):
        outputs = []
        for order in (FIELDS, tuple(reversed(FIELDS)), tuple(sorted(FIELDS))):
            with self.subTest(order=order):
                entries = [{key: entry[key] for key in order}
                           for entry in self.inputs["publication_entries"]]
                catalogue = json.loads(self.base_bytes)
                catalogue["scenes"].extend(
                    {key: entry[key] for key in FIELDS} for entry in entries)
                output = encode(catalogue)
                self.assertEqual(len(catalogue["scenes"]), 13)
                self.assertEqual(catalogue["scenes"][:11], self.base["scenes"])
                prefix = {**catalogue, "scenes": catalogue["scenes"][:11]}
                self.assertEqual(encode(prefix), self.base_bytes)
                self.assertEqual(hashlib.sha256(output).hexdigest(),
                                 self.inputs["catalogue_after_sha256"])
                self.assertTrue(output.endswith(b"\n"))
                self.assertFalse(output.endswith(b"\n\n"))
                for entry in catalogue["scenes"][11:]:
                    self.assertEqual(tuple(entry), FIELDS)
                outputs.append(output)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], outputs[2])


if __name__ == "__main__":
    unittest.main()
