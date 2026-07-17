"""spu_host — Python client for the RP2350/RP2040 southbridge USB CDC console.

Wraps the diagnostic console implemented in hardware/rp_common/spu_diag.c
(commands: status, manifold, scale, qr, hex, cfgtele, chord, rplu, ...),
which itself drives the frozen 8-opcode Southbridge SPI protocol
(docs/SOUTHBRIDGE_SPI_PROTOCOL.md) against the FPGA. Per the homogeneity
contract in knowledge/INTERCONNECT_ARCHITECTURE.md §2, this library is
written once against the console grammar and works unmodified against any
board the southbridge firmware targets (Tang 25K, Wukong A7 J11, ...).

License: MIT. See software/LICENSE.
"""

from .client import SPUHostClient, SPUProtocolError
from .som1 import SOM1FrameError, SOM1Result, parse_som1_frame

__all__ = [
    "SPUHostClient",
    "SPUProtocolError",
    "SOM1FrameError",
    "SOM1Result",
    "parse_som1_frame",
]
