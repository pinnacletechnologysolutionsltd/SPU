"""
SPU-13 Sovereign Geometry Library
Pre-calculated rational identity tables for Wildberger and Synergetics geometry.
No floating point. No approximation.
"""
from .rational_field import Frac, MultiSurd, S3, S5, S15, PHI, PHI_SQ
from .sovereign_lut import (
    IVM_SPREADS, SPREAD_LUT, JITTERBUG, TENSEGRITY_PRISM,
    TENSEGRITY_ICOSA, SYNERGETICS_VOLUMES, CONIC_SPREADS,
    triple_spread_check, triple_quad_check, spread_from_quadrances,
)
