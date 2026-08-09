"""Composition policy oracle — accept / hold / escalate.

Normative reference: docs/SERVICE_COMPOSITION_POLICY.md. This module is the
software oracle that RTL must match bit-exactly, in the same relationship as
software/lib/a31_field.py to the RPLU datapath.

Two properties are load-bearing and are asserted here rather than assumed:

1. **The SOM1 frame passes through untouched.** Composition never edits,
   recomputes or suppresses BMU evidence -- the frame this policy sees is the
   frame it forwards, byte for byte. `compose()` returns the original bytes
   object it was given, so a caller cannot accidentally forward a re-encoded
   copy that merely happens to be equal today.

2. **No new threshold is introduced.** Ambiguity is the classifier's own
   determination, carried in SOM1 flag bit 3 and already proven in silicon.
   The policy reads it; it does not second-guess it with a gap comparison of
   its own. This is what makes "thresholds fixed in RTL" cost nothing extra to
   re-prove: there is no new constant to prove.

There is deliberately no float anywhere in this module, and no comparison of
quadrances -- the policy is a function of flags and a verdict symbol only.
"""

from enum import Enum

from spu_host.som1 import parse_som1_frame


class Verdict(str, Enum):
    """What an algebra service (PHSLK, RPLU) may assert about a decision.

    Bounded and dimensionless by design -- see policy §1. An algebra service
    emits one of these; its internal field values never cross the boundary.
    """

    CONCUR = "concur"          # coherence established in the algebra's own domain
    DISSENT = "dissent"        # coherence not established
    UNAVAILABLE = "unavailable"  # service did not produce a verdict this cycle


class Outcome(str, Enum):
    """Policy §3. Advisory only -- the incumbent controller retains authority."""

    ACCEPT = "accept"      # BMU decision stands, algebra concurs
    HOLD = "hold"          # BMU decision stands but is not acted on
    ESCALATE = "escalate"  # referred outward; the coprocessor asserts nothing


class CompositionError(ValueError):
    pass


def compose(frame, verdict):
    """Apply the composition policy to one SOM1 frame and one algebra verdict.

    Returns (outcome, forwarded_frame, reason). `forwarded_frame` is the very
    object passed in -- identity, not equality -- because rule 3.1 is about
    the evidence being unchanged, not merely equal.
    """
    if not isinstance(verdict, Verdict):
        raise CompositionError("verdict must be a Verdict, got %r" % (verdict,))

    result = parse_som1_frame(frame)

    # Escalate before consulting the algebra at all: if the decision service
    # did not produce usable evidence, an algebra verdict cannot supply it.
    # PHSLK is a coherence predicate, not a classifier (policy §2).
    if not result.valid:
        return Outcome.ESCALATE, frame, "som1 result not valid"
    if result.error != 0:
        return Outcome.ESCALATE, frame, "som1 error code %d" % result.error
    if not result.map_valid:
        return Outcome.ESCALATE, frame, "som1 map not valid"
    if result.busy:
        return Outcome.ESCALATE, frame, "som1 classifier busy"

    # The classifier's own ambiguity call. No independent threshold: an
    # algebra predicate cannot rank two candidates, so it cannot break a tie
    # the classifier has already declared.
    if result.ambiguous:
        return Outcome.ESCALATE, frame, "som1 reported ambiguous"

    if verdict is Verdict.UNAVAILABLE:
        return Outcome.HOLD, frame, "algebra verdict unavailable"
    if verdict is Verdict.DISSENT:
        return Outcome.HOLD, frame, "algebra verdict dissents"
    return Outcome.ACCEPT, frame, "algebra verdict concurs"


def phslk_verdict(offer_num, offer_den, confirm_num, confirm_den):
    """PHSLK coherence by cross multiplication, as modelled in the arch sim.

    Exact integer comparison, zero tolerance. A zero denominator is not
    coherence and not a dissent -- it is an undefined comparison, so the
    service reports UNAVAILABLE rather than asserting something it cannot know.
    """
    if offer_den == 0 or confirm_den == 0:
        return Verdict.UNAVAILABLE
    left = offer_num * confirm_den
    right = confirm_num * offer_den
    return Verdict.CONCUR if left == right else Verdict.DISSENT
