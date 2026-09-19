# Example 1: Scalar Fibonacci Pulse

This program calculates Fibonacci numbers using exact arithmetic in $\mathbb{Q}(\sqrt{3})$.

## The Math
Each number is represented as a surd $(a + b\sqrt{3})$. For this pure integer example, $b = 0$.
Operations:
- `LD R0, 1, 0`: Load 1 into R0
- `ADD Rd, Rs1, Rs2`: Exact integer addition
- `LOG Rd`: Print register value and quadrance

## Running in the Emulator
```bash
spu sim examples/01_scalar_fibonacci/fibonacci.sas --steps 12
```
