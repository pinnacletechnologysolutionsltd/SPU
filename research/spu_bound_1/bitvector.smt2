; Separate 64-bit two's-complement bit-vector wrapping example.
(set-logic QF_BV)
(define-fun a () (_ BitVec 64) #x7fffffffffffffff)
(define-fun doubled () (_ BitVec 64) (bvmul a (_ bv2 64)))
; Wrapped doubled value is -2, whereas the exact product needs 65 signed bits.
(assert (distinct doubled #xfffffffffffffffe))
(check-sat)
