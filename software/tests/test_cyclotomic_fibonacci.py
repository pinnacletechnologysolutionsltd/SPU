#!/usr/bin/env python3
"""Characteristic-zero and M31-image oracle for Fibonacci braid arithmetic.

The test deliberately verifies the full multiplicity-free Pentagon and both
Hexagon paths.  F^2=I and the three-strand braid relation are useful checks,
but neither is accepted as a substitute for category coherence.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.cyclotomic_fibonacci import (
    CyclotomicDomain,
    FIBONACCI_F,
    FIBONACCI_IDENTITY,
    FIBONACCI_METRIC,
    FIBONACCI_R,
    FIBONACCI_SIGMA1,
    FIBONACCI_SIGMA1_INVERSE,
    FIBONACCI_SIGMA2,
    FIBONACCI_SIGMA2_INVERSE,
    M31,
    PHI,
    PHI_INVERSE,
    ZETA5_ONE,
    ZETA5_ZERO,
    ZETA5_ZETA,
    Zeta5,
    braid_growth_by_class,
    braid_storage_bits_by_class,
    braid_growth_profile,
    deterministic_braid_corpus,
    evaluate_braid_word,
    evaluate_braid_word_mod,
    hexagon_report,
    is_generic_label,
    matrix_dagger,
    matrix_identity,
    matrix_multiply,
    matrix_reduce_mod,
    pentagon_report,
    phi5_irreducible_over_prime,
    phi5_roots_mod_prime,
    signed_storage_bits,
    split_zero_divisor_pair,
    structured_pattern_orders,
)


CHECKS = 0
FAILURES = 0


def check(condition, message):
    global CHECKS, FAILURES
    CHECKS += 1
    if condition:
        print(f"  ok  {message}")
    else:
        FAILURES += 1
        print(f"  FAIL {message}")


def preserves_metric(matrix):
    return matrix_multiply(
        matrix_dagger(matrix), matrix_multiply(FIBONACCI_METRIC, matrix)
    ) == FIBONACCI_METRIC


print("== Z[zeta_5] ring ==")
check(ZETA5_ZETA**5 == ZETA5_ONE, "zeta^5 = 1 exactly")
check(
    sum((ZETA5_ZETA**power for power in range(5)), ZETA5_ZERO) == ZETA5_ZERO,
    "1+zeta+zeta^2+zeta^3+zeta^4 = 0",
)
check(
    PHI_INVERSE == Zeta5(-1, 0, -1, -1),
    "phi^-1 has the pinned canonical cyclotomic coefficients",
)
check(PHI == Zeta5(0, 0, -1, -1), "phi has the pinned canonical coefficients")
check(PHI * PHI_INVERSE == ZETA5_ONE, "phi*phi^-1 = 1")
root_fast_sample = Zeta5(7, -3, 11, 5)
check(
    root_fast_sample.multiply_by_zeta() == root_fast_sample * ZETA5_ZETA,
    "dedicated multiply-by-zeta equals general multiplication",
)
check(
    root_fast_sample.multiply_by_zeta() == Zeta5(-5, 2, -8, 6),
    "multiply-by-zeta is the pinned shift plus broadcast-subtract",
)
check(ZETA5_ZETA.trace() == -1, "Tr(zeta_5) = -1")
check(ZETA5_ZETA.norm() == 1, "N(zeta_5) = 1")
check(PHI.trace() == 2 and PHI.norm() == 1, "embedded phi trace/norm are exact")
check(
    all(
        root_fast_sample.automorphism(k).automorphism(j)
        == root_fast_sample.automorphism((k * j) % 5)
        for k in (1, 2, 3, 4)
        for j in (1, 2, 3, 4)
    ),
    "four Galois maps compose as (Z/5Z)^*",
)
check(
    root_fast_sample.conjugate().conjugate() == root_fast_sample,
    "complex conjugation is an involution",
)
check(
    root_fast_sample.domain is CyclotomicDomain.CHARACTERISTIC_ZERO_RING,
    "characteristic-zero operations retain explicit ring typestate",
)


print("\n== integral gauge and braid representation ==")
check(
    FIBONACCI_R
    == ((Zeta5(0, 0, 0, 1), ZETA5_ZERO),
        (ZETA5_ZERO, Zeta5(1, 1, 1, 1))),
    "R eigenvalues are zeta^3 and -zeta^4",
)
check(
    matrix_multiply(FIBONACCI_F, FIBONACCI_F) == FIBONACCI_IDENTITY,
    "integral-gauge F is its exact inverse",
)
ordinary_metric = matrix_identity(2, ZETA5_ONE)
check(
    matrix_multiply(
        matrix_dagger(FIBONACCI_F), matrix_multiply(ordinary_metric, FIBONACCI_F)
    )
    != ordinary_metric,
    "integral gauge is not Euclidean-unitary (intentional)",
)
for label, matrix in (
    ("F", FIBONACCI_F),
    ("R/sigma1", FIBONACCI_SIGMA1),
    ("sigma2", FIBONACCI_SIGMA2),
    ("sigma1^-1", FIBONACCI_SIGMA1_INVERSE),
    ("sigma2^-1", FIBONACCI_SIGMA2_INVERSE),
):
    check(preserves_metric(matrix), f"{label} preserves diag(1,phi) exactly")

check(
    matrix_multiply(FIBONACCI_SIGMA1_INVERSE, FIBONACCI_SIGMA1)
    == FIBONACCI_IDENTITY,
    "sigma1 inverse closes exactly",
)
check(
    matrix_multiply(FIBONACCI_SIGMA2_INVERSE, FIBONACCI_SIGMA2)
    == FIBONACCI_IDENTITY,
    "sigma2 inverse closes exactly",
)
left_braid = matrix_multiply(
    FIBONACCI_SIGMA1,
    matrix_multiply(FIBONACCI_SIGMA2, FIBONACCI_SIGMA1),
)
right_braid = matrix_multiply(
    FIBONACCI_SIGMA2,
    matrix_multiply(FIBONACCI_SIGMA1, FIBONACCI_SIGMA2),
)
check(left_braid == right_braid, "sigma1 sigma2 sigma1 = sigma2 sigma1 sigma2")


print("\n== category coherence ==")
pentagon_checked, pentagon_bad = pentagon_report()
hexagon_checked, hexagon_bad = hexagon_report()
check(pentagon_checked == 27, "Pentagon enumeration reaches 27 admissible sectors")
check(not pentagon_bad, f"complete multiplicity-free Pentagon catalog: {pentagon_bad}")
check(hexagon_checked == 24, "Hexagon enumeration reaches 24 directed identities")
check(not hexagon_bad, f"both complete Hexagon paths: {hexagon_bad}")


print("\n== fixed braid corpus and coefficient growth ==")
corpus = deterministic_braid_corpus(100)
profile = braid_growth_profile(100)
max_label = max(profile, key=profile.get)
max_bits = profile[max_label]
check(len(corpus) == 100, "declared corpus contains 100 deterministic braid words")
check(max(len(word) for word in corpus.values()) == 100, "corpus reaches length 100")
check(max_bits == 55, f"pinned maximum coefficient width is 55 bits ({max_label})")
# profile values are magnitude widths (abs(v).bit_length()), so a 64-bit signed
# guarantee needs magnitude <= 63, not <= 64. Check the storage width directly.
storage = braid_storage_bits_by_class(100)
check(
    max(storage.values()) <= 64,
    f"all corpus coefficients fit signed 64-bit storage: {storage}",
)
check(
    storage["structured"] == 56 and storage["generic"] == 15,
    f"signed storage widths are pinned at 56/15: {storage}",
)
check(
    signed_storage_bits(-(1 << 55)) == 56 and signed_storage_bits(1 << 55) == 57,
    "storage-width helper is asymmetric at the two's-complement boundary",
)

# Growth evidence has to be attributed honestly.  Three structured patterns
# generate finite cyclic subgroups and cannot grow at any length, so the
# stated bound must not be credited to the corpus as a whole.
orders = structured_pattern_orders()
check(
    orders["sigma1"] == 10 and orders["sigma2"] == 10 and orders["alternating"] == 15,
    f"finite-order patterns are pinned and cannot contribute growth: {orders}",
)
check(
    orders["inverse_alternating"] is None and orders["commutator"] is None,
    "the two growing structured patterns have no finite order within the cap",
)
by_class = braid_growth_by_class(100)
generic_labels = [label for label in profile if is_generic_label(label)]
check(len(generic_labels) == 50, "50 generic stream words back the growth claim")
check(
    by_class["structured"] == 55 and by_class["generic"] == 14,
    f"growth reported by class, not as one corpus-wide number: {by_class}",
)


print("\n== modular-domain separation and M31 image ==")
check(not phi5_irreducible_over_prime(521), "Phi_5 is reducible modulo 521")
check(
    phi5_roots_mod_prime(521) == [25, 104, 396, 516],
    "the four primitive fifth roots modulo 521 are pinned",
)
zero_factor, zero_cofactor = split_zero_divisor_pair(521, 25)
mod521_zero = ZETA5_ZERO.reduce_mod(521)
check(
    zero_factor != mod521_zero
    and zero_cofactor != mod521_zero
    and zero_factor * zero_cofactor == mod521_zero,
    "521 quotient has an explicit nonzero zero-divisor pair",
)
check(
    zero_factor.domain is CyclotomicDomain.MODULAR_QUOTIENT_RING,
    "521 value is tagged as a reducible modular quotient ring",
)
check(M31 % 5 == 2, "M31 lies in the irreducible residue class 2 mod 5")
check(phi5_irreducible_over_prime(M31), "Phi_5 is irreducible over F_M31")

sample = Zeta5(7, -3, 11, 5).reduce_mod(M31)
check(
    sample.domain is CyclotomicDomain.MODULAR_FIELD,
    "M31 value is tagged as an irreducible degree-4 modular field",
)
check(
    sample.multiply_by_zeta()
    == sample * ZETA5_ZETA.reduce_mod(M31),
    "modular multiply-by-zeta matches modular general multiplication",
)
check(sample * sample.inverse() == ZETA5_ONE.reduce_mod(M31), "sample M31 F_p^4 inverse")

try:
    _ = root_fast_sample + sample
    mixed_domain_rejected = False
except TypeError:
    mixed_domain_rejected = True
check(mixed_domain_rejected, "characteristic-zero/modular mixed arithmetic is rejected")

modular_mismatches = []
for label, word in corpus.items():
    characteristic_zero_image = matrix_reduce_mod(evaluate_braid_word(word), M31)
    modular_evaluation = evaluate_braid_word_mod(word, M31)
    if characteristic_zero_image != modular_evaluation:
        modular_mismatches.append(label)
check(
    not modular_mismatches,
    f"M31 evaluation equals reduction of characteristic-zero truth: {modular_mismatches}",
)


print("\n== predeclared feasibility gates ==")
g1 = not pentagon_bad and not hexagon_bad
g2 = (
    matrix_multiply(FIBONACCI_SIGMA1_INVERSE, FIBONACCI_SIGMA1)
    == FIBONACCI_IDENTITY
    and matrix_multiply(FIBONACCI_SIGMA2_INVERSE, FIBONACCI_SIGMA2)
    == FIBONACCI_IDENTITY
)
g3 = all(
    preserves_metric(matrix)
    for matrix in (
        FIBONACCI_SIGMA1,
        FIBONACCI_SIGMA2,
        FIBONACCI_SIGMA1_INVERSE,
        FIBONACCI_SIGMA2_INVERSE,
    )
)
g4 = (
    len(corpus) == 100
    and max(len(word) for word in corpus.values()) == 100
    and max_bits <= 64
    and all(
        isinstance(coefficient, int)
        for word in corpus.values()
        for row in evaluate_braid_word(word)
        for value in row
        for coefficient in value.coefficients
    )
)
g5 = phi5_irreducible_over_prime(M31) and not modular_mismatches
check(g1, "G1 coherence: 27 Pentagon sectors + 24 Hexagon identities, exact")
check(g2, "G2 inverses: both signed braid-generator round trips are identity")
check(g3, "G3 metric: both generators and inverses preserve diag(1,phi)")
check(
    g4,
    f"G4 growth: {len(corpus)} words through length 100, max magnitude "
    f"{max_bits} bits (structured {by_class['structured']}, generic "
    f"{by_class['generic']}); signed storage {storage['structured']}/"
    f"{storage['generic']}",
)
check(
    g5,
    f"G5 modular agreement: all {len(corpus)} M31 images match char-0 reduction",
)


print(f"\n{CHECKS - FAILURES} passed, {FAILURES} failed")
if FAILURES:
    print("CYCLOTOMIC FIBONACCI ORACLE: FAIL")
    sys.exit(1)
print("CYCLOTOMIC FIBONACCI ORACLE: ALL CHECKS PASS")
