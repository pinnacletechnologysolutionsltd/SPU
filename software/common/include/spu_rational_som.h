// spu_rational_som.h — exact rational/quadrance SOM reference model
//
// Software oracle for the first SPU-13 SOM/multicluster pass:
// weighted quadrance BMU selection, stable tie-breaking, confidence-gap
// calculation, and Nguyen-style cluster label reduction.
//
// No floating point. No square root. No division in the BMU hot path.

#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include "spu_surd.h"
#include "spu_quadray.h"

struct SomAxialCoord {
    int16_t q;
    int16_t r;
};

constexpr SomAxialCoord SOM_HEX_DELTAS[6] = {
    {  1,  0 },
    {  1, -1 },
    {  0, -1 },
    { -1,  0 },
    { -1,  1 },
    {  0,  1 },
};

inline SomAxialCoord som_hex_neighbor(const SomAxialCoord& c, int dir) {
    const SomAxialCoord d = SOM_HEX_DELTAS[dir % 6];
    return SomAxialCoord{
        static_cast<int16_t>(c.q + d.q),
        static_cast<int16_t>(c.r + d.r),
    };
}

template <std::size_t FEATURES>
struct SomNode {
    uint16_t node_id = 0;
    SomAxialCoord coord { 0, 0 };
    uint16_t cluster_label = 0;
    std::array<RationalSurd, FEATURES> weights {};
    bool valid = true;
};

struct SomBmuResult {
    bool valid = false;
    bool has_second = false;
    uint16_t best_node_id = 0xFFFFu;
    uint16_t second_node_id = 0xFFFFu;
    uint16_t cluster_label = 0;
    RationalSurd best_q {};
    RationalSurd second_q {};
    RationalSurd confidence_gap {};

    bool exact_tie() const {
        return has_second && confidence_gap.is_zero();
    }
};

template <std::size_t FEATURES>
inline RationalSurd som_weighted_quadrance(
    const std::array<RationalSurd, FEATURES>& features,
    const std::array<RationalSurd, FEATURES>& node_weights,
    const std::array<RationalSurd, FEATURES>& feature_weights
) {
    RationalSurd total;
    for (std::size_t i = 0; i < FEATURES; i++) {
        RationalSurd delta = features[i] - node_weights[i];
        total += feature_weights[i] * delta.quadrance();
    }
    return total;
}

inline bool som_score_better(const RationalSurd& cand_q,
                             uint16_t cand_id,
                             const RationalSurd& ref_q,
                             uint16_t ref_id,
                             bool has_ref) {
    if (!has_ref)
        return true;
    if (rs_lt(cand_q, ref_q))
        return true;
    return cand_q == ref_q && cand_id < ref_id;
}

template <std::size_t FEATURES, std::size_t NODES>
inline SomBmuResult som_find_bmu(
    const std::array<RationalSurd, FEATURES>& features,
    const std::array<SomNode<FEATURES>, NODES>& nodes,
    const std::array<RationalSurd, FEATURES>& feature_weights
) {
    SomBmuResult out;

    for (const auto& node : nodes) {
        if (!node.valid)
            continue;

        RationalSurd q_i = som_weighted_quadrance(
            features, node.weights, feature_weights);

        if (som_score_better(q_i, node.node_id,
                             out.best_q, out.best_node_id, out.valid)) {
            if (out.valid) {
                out.second_node_id = out.best_node_id;
                out.second_q = out.best_q;
                out.has_second = true;
            }
            out.valid = true;
            out.best_node_id = node.node_id;
            out.best_q = q_i;
            out.cluster_label = node.cluster_label;
        } else if (som_score_better(q_i, node.node_id,
                                    out.second_q, out.second_node_id,
                                    out.has_second)) {
            out.second_node_id = node.node_id;
            out.second_q = q_i;
            out.has_second = true;
        }
    }

    if (out.valid && out.has_second)
        out.confidence_gap = out.second_q - out.best_q;
    return out;
}

inline bool som_rs_le(const RationalSurd& lhs, const RationalSurd& rhs) {
    return lhs == rhs || rs_lt(lhs, rhs);
}

struct SomClusterResult {
    uint16_t label = 0;
    bool ambiguous = false;
};

inline SomClusterResult som_cluster_reduce(
    const SomBmuResult& result,
    const RationalSurd& ambiguity_threshold = SURD_ZERO
) {
    return SomClusterResult{
        result.cluster_label,
        result.has_second && som_rs_le(result.confidence_gap, ambiguity_threshold),
    };
}

