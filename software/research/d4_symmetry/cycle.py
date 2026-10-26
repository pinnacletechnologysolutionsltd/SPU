"""Exact ordered composition and cycle checks for typed W(D4) edges."""

from software.research.lattice_comparison import d4

from .canonical import GROUP, IDENTITY
from .types import GroupElementD4, RelationEdge


IDENTITY_D4 = GroupElementD4(IDENTITY)


def compose(left, right):
    """Compose group elements; apply right first, then left."""
    if not isinstance(left, GroupElementD4) or not isinstance(right, GroupElementD4):
        raise ValueError("D4_TYPED_COMPOSITION")
    return GroupElementD4(d4.compose(left.descriptor, right.descriptor))


def inverse(element):
    if not isinstance(element, GroupElementD4):
        raise ValueError("D4_TYPED_INVERSE")
    for candidate in GROUP:
        if (d4.compose(candidate, element.descriptor) == IDENTITY
                and d4.compose(element.descriptor, candidate) == IDENTITY):
            return GroupElementD4(candidate)
    raise ValueError("D4_NO_INVERSE")


def act(element, coordinates):
    if not isinstance(element, GroupElementD4):
        raise ValueError("D4_TYPED_ACTION")
    return d4.act(element.descriptor, coordinates)


def compose_edges(path):
    """Return the ordered product for a contiguous, closed directed edge path."""
    if type(path) not in (tuple, list) or not path:
        raise ValueError("D4_CYCLE_PATH")
    if any(not isinstance(edge, RelationEdge) for edge in path):
        raise ValueError("D4_CYCLE_EDGE")
    for current, following in zip(path, path[1:]):
        if current.target != following.source:
            raise ValueError("D4_CYCLE_DISCONTIGUOUS")
    if path[-1].target != path[0].source:
        raise ValueError("D4_CYCLE_OPEN")
    product = IDENTITY_D4
    for edge in path:
        product = compose(edge.element, product)
    return product


def edge_from_frames(source, target, source_frame, target_frame):
    """Build source→target transform from global-to-frame gauge assignments."""
    if not isinstance(source_frame, GroupElementD4) or not isinstance(target_frame, GroupElementD4):
        raise ValueError("D4_FRAME_ASSIGNMENT")
    return RelationEdge(source, target, compose(target_frame, inverse(source_frame)))


def matches_expected(path, expected):
    if not isinstance(expected, GroupElementD4):
        raise ValueError("D4_EXPECTED_PRODUCT")
    return compose_edges(path) == expected
