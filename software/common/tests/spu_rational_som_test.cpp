// spu_rational_som_test.cpp — exact rational SOM/BMU tests

#include <array>
#include <cstdio>
#include "spu_rational_som.h"

static int failures = 0;

#define CHECK(label, cond) do { \
    if (!(cond)) { printf("  FAIL: %s\n", label); failures++; } \
} while(0)

#define CHECK_SURD(label, got, want) do { \
    RationalSurd _g=(got), _w=(want); \
    if (_g != _w) { \
        printf("  FAIL: %s  got (%d,%d) want (%d,%d)\n", \
               label, _g.p, _g.q, _w.p, _w.q); \
        failures++; \
    } \
} while(0)

using Node4 = SomNode<4>;
using Vec4 = std::array<RationalSurd, 4>;

static constexpr RationalSurd rs(int32_t p, int32_t q = 0) {
    return RationalSurd(p, q);
}

static std::array<Node4, 7> tiny_hex_nodes() {
    return {{
        Node4{0, { 0,  0}, 0, Vec4{rs( 0), rs( 0), rs( 0), rs(0)}},
        Node4{1, { 1,  0}, 1, Vec4{rs( 2), rs( 0), rs( 0), rs(0)}},
        Node4{2, { 1, -1}, 1, Vec4{rs( 0), rs( 2), rs( 0), rs(0)}},
        Node4{3, { 0, -1}, 2, Vec4{rs( 0), rs( 0), rs( 2), rs(0)}},
        Node4{4, {-1,  0}, 2, Vec4{rs(-2), rs( 0), rs( 0), rs(0)}},
        Node4{5, {-1,  1}, 3, Vec4{rs( 0), rs(-2), rs( 0), rs(0)}},
        Node4{6, { 0,  1}, 3, Vec4{rs( 0), rs( 0), rs(-2), rs(1, 1)}},
    }};
}

static Vec4 feature_weights() {
    return Vec4{rs(1), rs(2), rs(1), rs(1)};
}

static void test_integer_bmu() {
    auto nodes = tiny_hex_nodes();
    auto fweights = feature_weights();
    Vec4 features { rs(2), rs(1), rs(0), rs(0) };

    SomBmuResult r = som_find_bmu(features, nodes, fweights);
    SomClusterResult c = som_cluster_reduce(r);

    CHECK("integer BMU valid", r.valid);
    CHECK("integer BMU best node", r.best_node_id == 1);
    CHECK("integer BMU second node stable tie", r.second_node_id == 0);
    CHECK("integer BMU cluster label", r.cluster_label == 1);
    CHECK_SURD("integer BMU best_q", r.best_q, rs(2));
    CHECK_SURD("integer BMU second_q", r.second_q, rs(6));
    CHECK_SURD("integer BMU confidence gap", r.confidence_gap, rs(4));
    CHECK("integer BMU not ambiguous", !c.ambiguous);
}

static void test_surd_bmu() {
    auto nodes = tiny_hex_nodes();
    auto fweights = feature_weights();
    Vec4 features { rs(0), rs(0), rs(-2), rs(2, 1) };

    SomBmuResult r = som_find_bmu(features, nodes, fweights);

    CHECK("surd BMU best node", r.best_node_id == 6);
    CHECK("surd BMU cluster label", r.cluster_label == 3);
    CHECK_SURD("surd BMU best_q", r.best_q, rs(1));
    CHECK("surd BMU has second", r.has_second);
    CHECK("surd BMU gap positive", rs_lt(rs(0), r.confidence_gap));
}

static void test_weighted_quadrance_field_square() {
    std::array<RationalSurd, 1> features { rs(2, 1) };
    std::array<RationalSurd, 1> weights { rs(0) };
    std::array<RationalSurd, 1> rweights { rs(1) };

    RationalSurd got = som_weighted_quadrance(features, weights, rweights);
    CHECK_SURD("(2+sqrt3)^2 uses field square", got, rs(7, 4));
}

static void test_stable_tie_breaking() {
    using Node1 = SomNode<1>;
    std::array<Node1, 3> nodes {{
        Node1{5, {0, 0}, 9, std::array<RationalSurd, 1>{rs(0)}},
        Node1{1, {1, 0}, 7, std::array<RationalSurd, 1>{rs(0)}},
        Node1{3, {0, 1}, 8, std::array<RationalSurd, 1>{rs(0)}},
    }};
    std::array<RationalSurd, 1> features { rs(0) };
    std::array<RationalSurd, 1> fweights { rs(1) };

    SomBmuResult r = som_find_bmu(features, nodes, fweights);
    SomClusterResult c = som_cluster_reduce(r);

    CHECK("tie best lowest node id", r.best_node_id == 1);
    CHECK("tie second next-lowest node id", r.second_node_id == 3);
    CHECK_SURD("tie zero gap", r.confidence_gap, rs(0));
    CHECK("tie classified ambiguous", c.ambiguous);
    CHECK("tie cluster follows best", c.label == 7);
}

static void test_invalid_nodes_are_skipped() {
    using Node1 = SomNode<1>;
    std::array<Node1, 2> nodes {{
        Node1{0, {0, 0}, 1, std::array<RationalSurd, 1>{rs(0)}, false},
        Node1{1, {1, 0}, 2, std::array<RationalSurd, 1>{rs(3)}, true},
    }};
    std::array<RationalSurd, 1> features { rs(0) };
    std::array<RationalSurd, 1> fweights { rs(1) };

    SomBmuResult r = som_find_bmu(features, nodes, fweights);

    CHECK("invalid node skipped best", r.best_node_id == 1);
    CHECK("invalid node skipped no second", !r.has_second);
}

static void test_hex_neighbor_deltas() {
    SomAxialCoord c {0, 0};
    const SomAxialCoord expected[6] = {
        {1, 0}, {1, -1}, {0, -1}, {-1, 0}, {-1, 1}, {0, 1},
    };
    for (int i = 0; i < 6; i++) {
        SomAxialCoord got = som_hex_neighbor(c, i);
        if (got.q != expected[i].q || got.r != expected[i].r) {
            printf("  FAIL: hex neighbor %d got (%d,%d) want (%d,%d)\n",
                   i, got.q, got.r, expected[i].q, expected[i].r);
            failures++;
        }
    }
}

int main() {
    test_integer_bmu();
    test_surd_bmu();
    test_weighted_quadrance_field_square();
    test_stable_tie_breaking();
    test_invalid_nodes_are_skipped();
    test_hex_neighbor_deltas();

    if (failures == 0) {
        printf("PASS\n");
        return 0;
    }
    printf("FAIL (%d failures)\n", failures);
    return 1;
}
