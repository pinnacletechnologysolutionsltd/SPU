# generate_thomson_nodals.py
def to_spu24(val):
    """Formats a value into a 24-bit Hex for iCE40 BRAM."""
    return f"{val & 0xFFFFFF:06X}"

# These are the 13 Primes that anchor the 13D Field
# We use the 'Stiff' prime set starting at 5 to avoid 
# low-order interference in the 15-Sigma Snap.
THOMSON_NODALS = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

def generate_mem():
    with open("spu_primes.mem", "w") as f:
        f.write("// SPU-13: f=4 Geodesic Nodal Anchors\n")
        for addr, prime in enumerate(THOMSON_NODALS):
            # We map the prime to the 'a' (rational) component [23:18]
            # or as a direct 24-bit literal depending on your ALU config.
            hex_data = to_spu24(prime)
            f.write(f"@{addr:02X} {hex_data}\n")
    print("✅ spu_primes.mem generated. Ready for BRAM Hydration.")

if __name__ == "__main__":
    generate_mem()
