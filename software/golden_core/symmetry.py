"""Exact full symmetry classification of the reference icosahedron."""

from dataclasses import dataclass

from .exact import ONE, Q5, ZERO
from .icosahedron import Vec3, edges, faces, vertices

Matrix3 = tuple[tuple[Q5, Q5, Q5], tuple[Q5, Q5, Q5], tuple[Q5, Q5, Q5]]


def determinant(matrix: Matrix3) -> Q5:
    a, b, c = matrix
    return (a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0]))


def _inverse(matrix: Matrix3) -> Matrix3:
    det = determinant(matrix)
    if det == ZERO:
        raise ValueError("basis matrix is singular")
    cofactors = []
    for row in range(3):
        out = []
        for col in range(3):
            minor = [[matrix[r][c] for c in range(3) if c != col]
                     for r in range(3) if r != row]
            value = minor[0][0] * minor[1][1] - minor[0][1] * minor[1][0]
            out.append(value if (row + col) % 2 == 0 else -value)
        cofactors.append(out)
    return tuple(tuple(cofactors[col][row] / det for col in range(3))
                 for row in range(3))  # type: ignore[return-value]


def _matmul(left: Matrix3, right: Matrix3) -> Matrix3:
    return tuple(tuple(sum((left[i][k] * right[k][j] for k in range(3)), ZERO)
                       for j in range(3)) for i in range(3))  # type: ignore[return-value]


def _transpose(matrix: Matrix3) -> Matrix3:
    return tuple(tuple(matrix[j][i] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def _apply(matrix: Matrix3, point: Vec3) -> Vec3:
    coords = (point.x, point.y, point.z)
    result = tuple(sum((matrix[i][j] * coords[j] for j in range(3)), ZERO)
                   for i in range(3))
    return Vec3(*result)


@dataclass(frozen=True)
class Symmetry:
    """One exact orthogonal map, represented by its vertex permutation."""

    vertex_image: tuple[int, ...]
    matrix: Matrix3
    determinant: int

    @property
    def proper(self) -> bool:
        return self.determinant == 1

    def preserves_attributes(self, labels=None, weights=None) -> bool:
        """Whether this map preserves supplied per-vertex data exactly."""
        for values in (labels, weights):
            if values is not None:
                if len(values) != len(self.vertex_image):
                    raise ValueError("attribute vector must have one value per vertex")
                if any(values[i] != values[self.vertex_image[i]]
                       for i in range(len(values))):
                    return False
        return True


def _independent_basis(points: tuple[Vec3, ...]) -> tuple[int, int, int]:
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            for k in range(j + 1, len(points)):
                columns = ((points[i].x, points[j].x, points[k].x),
                           (points[i].y, points[j].y, points[k].y),
                           (points[i].z, points[j].z, points[k].z))
                if determinant(columns) != ZERO:
                    return i, j, k
    raise ValueError("vertices do not span three dimensions")


def icosahedral_symmetries() -> tuple[Symmetry, ...]:
    """Enumerate graph automorphisms and derive/check each exact linear map.

    Backtracking preserves adjacency and non-adjacency. Since the vertex set
    spans three dimensions, each permutation determines a unique linear map;
    exact checks then establish orthogonality and determinant sign.
    """
    points = vertices()
    edge_list = edges(points)
    edge_set = set(edge_list)
    adjacency = [set() for _ in points]
    for i, j in edge_list:
        adjacency[i].add(j)
        adjacency[j].add(i)
    images = [-1] * len(points)
    used: set[int] = set()
    permutations: list[tuple[int, ...]] = []

    def search(source: int) -> None:
        if source == len(points):
            permutations.append(tuple(images))
            return
        for target in range(len(points)):
            if target in used:
                continue
            if all(((prior in adjacency[source]) ==
                    (images[prior] in adjacency[target]))
                   for prior in range(source)):
                images[source] = target
                used.add(target)
                search(source + 1)
                used.remove(target)
                images[source] = -1

    search(0)
    basis_indices = _independent_basis(points)
    source_columns = tuple(tuple((points[index].x, points[index].y, points[index].z)[row]
                                 for index in basis_indices) for row in range(3))
    source_inverse = _inverse(source_columns)  # type: ignore[arg-type]
    identity: Matrix3 = ((ONE, ZERO, ZERO), (ZERO, ONE, ZERO), (ZERO, ZERO, ONE))
    result = []
    index_of = {point: i for i, point in enumerate(points)}
    for permutation in permutations:
        target_columns = tuple(tuple((points[permutation[index]].x,
                                      points[permutation[index]].y,
                                      points[permutation[index]].z)[row]
                                     for index in basis_indices) for row in range(3))
        matrix = _matmul(target_columns, source_inverse)  # type: ignore[arg-type]
        if any(_apply(matrix, point) != points[permutation[i]]
               for i, point in enumerate(points)):
            raise AssertionError("graph automorphism is not induced by its exact linear map")
        if _matmul(_transpose(matrix), matrix) != identity:
            raise AssertionError("icosahedron symmetry is not orthogonal")
        det = determinant(matrix)
        if det not in (ONE, -ONE):
            raise AssertionError("orthogonal map determinant is not ±1")
        mapped_edges = {(min(permutation[i], permutation[j]),
                         max(permutation[i], permutation[j])) for i, j in edge_list}
        if mapped_edges != edge_set:
            raise AssertionError("symmetry does not preserve edges")
        face_set = set(faces(points))
        mapped_faces = {tuple(sorted(permutation[i] for i in face)) for face in face_set}
        if mapped_faces != face_set:
            raise AssertionError("symmetry does not preserve faces")
        # A second exact check: each matrix image equals its indexed vertex.
        if tuple(index_of[_apply(matrix, p)] for p in points) != permutation:
            raise AssertionError("matrix and permutation disagree")
        result.append(Symmetry(permutation, matrix, 1 if det == ONE else -1))
    return tuple(sorted(result, key=lambda symmetry: symmetry.vertex_image))
