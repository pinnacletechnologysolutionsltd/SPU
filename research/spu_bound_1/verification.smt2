; QF_NIA: all variables are mathematical integers, not machine words.
(set-logic QF_NIA)
(declare-const a Int)(declare-const b Int)(declare-const c Int)(declare-const d Int)
(assert (and (<= -2 a) (<= a 2) (<= -2 b) (<= b 2) (<= -2 c) (<= c 2) (<= -2 d) (<= d 2)))
(define-fun A () Int (+ (* a c) (* 3 b d)))
(define-fun B () Int (+ (* a d) (* b c)))
(define-fun N () Int (- (* c c) (* 3 d d)))
; F1 coefficient interval; F2 imaginary cancellation; F3 norm identity.
(push)(assert (or (< A -16) (> A 16) (< B -8) (> B 8)))(check-sat)(pop)
(push)(assert (distinct (+ (* a (- b)) (* b a)) 0))(check-sat)(pop)
(push)(assert (or (distinct (- (* A c) (* 3 B d)) (* a N)) (distinct (- (* B c) (* A d)) (* b N))))(check-sat)(pop)
; F3 exact final bounds.
(push)(assert (or (< (* a N) -24) (> (* a N) 24) (< (* b N) -24) (> (* b N) 24)))(check-sat)(pop)
; F4 correlation. Treating variables independent cannot establish B=0.
(push)(assert (and (= c a) (= d (- b)) (distinct B 0)))(check-sat)(pop)
; wrong multiplication coefficient.
(push)(assert (distinct (+ (* a c) (* b d)) A))(check-sat)(get-value (a b c d A))(pop)
; invalid independence: assuming B always zero without correlation.
(push)(assert (distinct B 0))(check-sat)(get-value (a b c d B))(pop)
; incorrect corner-only lower bound a²>=4.
(push)(assert (< (* a a) 4))(check-sat)(get-value (a))(pop)
; wrong norm sign.
(push)(assert (distinct N (+ (* c c) (* 3 d d))))(check-sat)(get-value (c d N))(pop)
