"""Named TGR1 golden fixtures for the first tensegrity sidecar probe."""

from __future__ import annotations

from dataclasses import dataclass

from .tensegrity_balancer import (
    Edge,
    EdgeType,
    GridState,
    PHI_ONE,
    TensegrityFault,
    TensegrityState,
    TensegritySystem,
    Vec3Phi,
    make_tensegrity_antipodal_counterexample,
    make_tensegrity_six_strut,
)


@dataclass(frozen=True)
class TensegrityGoldenVector:
    vector_id: int
    name: str
    system: TensegritySystem
    expected_state: TensegrityState
    expected_fault: TensegrityFault


def _topology_fault() -> TensegritySystem:
    return TensegritySystem(
        nodes=[Vec3Phi.origin() for _ in range(6)],
        grid_states=[GridState.MAIN] * 6,
        edges=[
            Edge(0, 1, EdgeType.STRUT), Edge(0, 2, EdgeType.STRUT),
            Edge(1, 2, EdgeType.STRUT), Edge(3, 4, EdgeType.STRUT),
            Edge(3, 5, EdgeType.STRUT), Edge(4, 5, EdgeType.STRUT),
        ],
    )


def golden_vectors() -> tuple[TensegrityGoldenVector, ...]:
    """Return fresh, deterministic systems in their fixed vector-id order."""

    balanced = make_tensegrity_six_strut()

    collision = make_tensegrity_six_strut()
    struts = [i for i, edge in enumerate(collision.edges)
              if edge.edge_type == EdgeType.STRUT]
    collision.edges[struts[1]] = Edge(0, 9, EdgeType.STRUT)

    slack = make_tensegrity_six_strut()
    for edge in slack.edges:
        if edge.edge_type == EdgeType.CABLE:
            slack.nodes[edge.node_b] = slack.nodes[edge.node_a]
            break

    intersection = make_tensegrity_antipodal_counterexample()

    mismatch = make_tensegrity_six_strut()
    mismatch.grid_states[0] = GridState.CONJ

    non_equilibrium = make_tensegrity_six_strut()
    node = non_equilibrium.nodes[0]
    non_equilibrium.nodes[0] = Vec3Phi(node.x + PHI_ONE, node.y, node.z)

    return (
        TensegrityGoldenVector(0, "canonical_balanced", balanced,
                               TensegrityState.BALANCED, TensegrityFault.NONE),
        TensegrityGoldenVector(1, "fault_topology", _topology_fault(),
                               TensegrityState.FAULT_TOPOLOGY,
                               TensegrityFault.TOPOLOGY_ERROR),
        TensegrityGoldenVector(2, "fault_strut_collision", collision,
                               TensegrityState.FAULT_STRUT_COLLISION,
                               TensegrityFault.STRUT_COLLISION),
        TensegrityGoldenVector(3, "fault_cable_slack", slack,
                               TensegrityState.FAULT_CABLE_SLACK,
                               TensegrityFault.CABLE_SLACK),
        TensegrityGoldenVector(4, "fault_strut_intersection", intersection,
                               TensegrityState.FAULT_STRUT_INTERSECTION,
                               TensegrityFault.STRUT_INTERSECTION),
        TensegrityGoldenVector(5, "fault_grid_mismatch", mismatch,
                               TensegrityState.FAULT_GRID_MISMATCH,
                               TensegrityFault.GRID_MISMATCH),
        TensegrityGoldenVector(6, "fault_not_in_equilibrium", non_equilibrium,
                               TensegrityState.FAULT_NOT_IN_EQUILIBRIUM,
                               TensegrityFault.NOT_IN_EQUILIBRIUM),
    )


def run_oracle(system: TensegritySystem) -> tuple[TensegrityState, TensegrityFault]:
    """Execute the state-machine sequence used by the sidecar contract."""

    system.configure()
    if system.state == TensegrityState.CONFIGURING:
        system.verify_balance()
    return system.state, system.fault
