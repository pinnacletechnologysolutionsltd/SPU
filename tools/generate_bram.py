# generate_bram.py - SPU-13 Anchor Generator
def to_surd_hex(a, b, c):
    """Converts a, b, c components to a 24-bit hex string."""
    val = ((a & 0x3F) << 18) | ((b & 0x1FF) << 9) | (c & 0x1FF)
    return f"{val:06X}"

# Define our 15-Sigma Anchors
anchors = [
    to_surd_hex(1, 0, 0),    # Unity
    to_surd_hex(0, 1, 0),    # sqrt(3) anchor
    to_surd_hex(0, 0, 1),    # sqrt(5) anchor
    "01A785",               # PHI_1 (Example)
    "010000"                # S_HALF (Example)
]

with open("spu_init.mem", "w") as f:
    for addr, hex_val in enumerate(anchors):
        f.write(f"@{addr:02X} {hex_val}\n")

print("Memory Map 'spu_init.mem' generated for iCE40 BRAM.")
