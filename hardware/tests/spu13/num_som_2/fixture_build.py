"""Derive the NUM-SOM-2 experimental fixture text from the production spu_som_bmu.v (single source of truth)."""
import hashlib
import re

OLD = ("    wire signed [32:0] da = $signed({1'b0, lhs[63:32]})\n"
       "                                  - $signed({1'b0, rhs[63:32]});")
NEW = ("    wire signed [32:0] da = $signed({lhs[63], lhs[63:32]})\n"
       "                                  - $signed({rhs[63], rhs[63:32]});")


def header(prod_text):
    sha = hashlib.sha256(prod_text.encode()).hexdigest()
    return ("// FIXTURE: EXPERIMENTAL TEST FIXTURE -- NOT PRODUCTION RTL, NOT AN IMPLEMENTATION PROPOSAL OF RECORD.\n"
            "// FIXTURE: Derived from hardware/rtl/core/spu13/spu_som_bmu.v; modules renamed *_expsgn so they can be\n"
            "// FIXTURE: compiled beside the production modules. Only functional change: the comparator's upper (P)\n"
            "// FIXTURE: half is sign-extended instead of zero-extended in `da`.\n"
            f"// FIXTURE: PRODUCTION-SHA256: {sha}\n")


def body(prod_text):
    t = re.sub(r"\bspu_som_bmu\b", "spu_som_bmu_expsgn", prod_text)
    t = re.sub(r"\bspu_surd_lt_serial\b", "spu_surd_lt_serial_expsgn", t)
    assert t.count(OLD) == 1, "comparator da expression not found exactly once"
    return t.replace(OLD, NEW)


def fixture(prod_text):
    return header(prod_text) + body(prod_text)
