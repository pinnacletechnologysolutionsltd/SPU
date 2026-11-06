; Integer arithmetic; finite box input, no machine-state claims.
(set-logic QF_LIA)
(declare-const a Int)
(declare-const b Int)
(assert (and (<= -2 a) (<= a 2) (<= -2 b) (<= b 2)))
(define-fun x () Int (+ (* 2 a) (* 3 b)))
(define-fun y () Int (+ a (* 2 b)))
; Prove sharp first-prefix bound [-10,10] x [-6,6].
(push)(assert (or (< x -10) (> x 10) (< y -6) (> y 6)))(check-sat)(pop)
; Prove reconstruction and hence final exact box after U,V.
(push)(assert (or (distinct (- (* 2 x) (* 3 y)) a) (distinct (- (* 2 y) x) b)))(check-sat)(pop)
; Wrong but tempting bound: each output bounded by largest input times 2.
(push)(assert (or (< x -4) (> x 4)))(check-sat)(get-value (a b x))(pop)
; Wrong inverse control.
(push)(assert (distinct (+ (* 2 x) (* 3 y)) a))(check-sat)(get-value (a b x y))(pop)
; Tightness: witnesses attain both positive upper bounds simultaneously.
(push)(assert (and (= x 10) (= y 6)))(check-sat)(get-value (a b))(pop)
