"""Immutable, runtime-checked values for exact W(D4) relationship graphs."""

from dataclasses import dataclass

from software.research.lattice_comparison import d4


_GROUP = frozenset(d4.group())


@dataclass(frozen=True, order=True)
class FrameID:
    value: str

    def __post_init__(self):
        if type(self.value) is not str or not self.value:
            raise ValueError("D4_FRAME_ID")


@dataclass(frozen=True)
class GroupElementD4:
    descriptor: tuple

    def __post_init__(self):
        try:
            d4.validate(self.descriptor)
        except (TypeError, ValueError) as exc:
            raise ValueError("D4_GROUP_ELEMENT") from exc
        normalized = (tuple(self.descriptor[0]), tuple(self.descriptor[1]))
        if normalized not in _GROUP:
            raise ValueError("D4_GROUP_ELEMENT")
        object.__setattr__(self, "descriptor", normalized)


@dataclass(frozen=True)
class SymmetryState:
    representation: str
    frame: FrameID
    coordinates: tuple

    def __post_init__(self):
        if type(self.representation) is not str or not self.representation:
            raise ValueError("D4_REPRESENTATION")
        if not isinstance(self.frame, FrameID):
            raise ValueError("D4_STATE_FRAME")
        if (type(self.coordinates) not in (tuple, list)
                or len(self.coordinates) != 4
                or any(type(value) is not int for value in self.coordinates)):
            raise ValueError("D4_STATE_COORDINATES")
        object.__setattr__(self, "coordinates", tuple(self.coordinates))


@dataclass(frozen=True)
class TransformWitness:
    source: FrameID
    target: FrameID
    element: GroupElementD4

    def __post_init__(self):
        if not isinstance(self.source, FrameID) or not isinstance(self.target, FrameID):
            raise ValueError("D4_WITNESS_FRAME")
        if not isinstance(self.element, GroupElementD4):
            raise ValueError("D4_WITNESS_ELEMENT")


@dataclass(frozen=True)
class OrbitKey:
    representation: str
    canonical_coordinates: tuple

    def __post_init__(self):
        if type(self.representation) is not str or not self.representation:
            raise ValueError("D4_REPRESENTATION")
        if (type(self.canonical_coordinates) not in (tuple, list)
                or len(self.canonical_coordinates) != 4
                or any(type(value) is not int for value in self.canonical_coordinates)):
            raise ValueError("D4_ORBIT_COORDINATES")
        object.__setattr__(self, "canonical_coordinates", tuple(self.canonical_coordinates))


@dataclass(frozen=True)
class RelationEdge:
    source: FrameID
    target: FrameID
    element: GroupElementD4

    def __post_init__(self):
        if not isinstance(self.source, FrameID) or not isinstance(self.target, FrameID):
            raise ValueError("D4_EDGE_FRAME")
        if not isinstance(self.element, GroupElementD4):
            raise ValueError("D4_EDGE_ELEMENT")
