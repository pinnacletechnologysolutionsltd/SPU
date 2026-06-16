// spu_rational_robotics_test.cpp — rational robotics inverse-closure tests

#include <array>
#include <cstdio>
#include "spu_rational_robotics.h"

static int failures = 0;

#define CHECK(label, cond) do { \
    if (!(cond)) { printf("  FAIL: %s\n", label); failures++; } \
} while(0)

#define CHECK_Q3(label, got, want) do { \
    RationalQ3 _g=(got), _w=(want); \
    if (_g != _w) { \
        printf("  FAIL: %s  got (%lld,%lld)/%lld want (%lld,%lld)/%lld\n", \
               label, (long long)_g.p, (long long)_g.q, (long long)_g.den, \
               (long long)_w.p, (long long)_w.q, (long long)_w.den); \
        failures++; \
    } \
} while(0)

static void test_pell_inverse_closure() {
    CHECK_Q3("Pell forward inverse scalar = 1", q3(2, 1) * q3(2, -1), q3(1));

    RoboticsQuadray v0 = robotics_sample_vector();
    RoboticsQuadray v1 = robotics_pell_step(v0, 7);
    RoboticsQuadray v2 = robotics_pell_step(v1, -7);

    CHECK("Pell trajectory closes after inverse steps", robotics_is_closed(v0, v2));
    CHECK("forward-only Pell step is not closed", !robotics_is_closed(v0, v1));
}

static void test_circulant_inverse_coefficients() {
    RoboticsJoint j60 = robotics_joint_60(3);
    RoboticsJoint inv = robotics_circulant_inverse(j60);
    RoboticsJoint j240 = robotics_joint_240(3);

    CHECK_Q3("60-degree determinant = 1", robotics_circulant_determinant(j60), q3(1));
    CHECK_Q3("inverse of 60 has F=2/3", inv.f, q3(2, 0, 3));
    CHECK_Q3("inverse of 60 has G=-1/3", inv.g, q3(-1, 0, 3));
    CHECK_Q3("inverse of 60 has H=2/3", inv.h, q3(2, 0, 3));
    CHECK("inverse of 60 equals 240-degree joint", inv == j240);
}

static void test_recalculated_rotation_catalog() {
    std::array<RoboticsJoint, 6> joints {
        robotics_joint_identity(),
        robotics_joint_60(),
        robotics_joint_240(),
        robotics_joint_120(),
        robotics_joint_p5_forward(),
        robotics_joint_p5_inverse(),
    };

    for (const auto& j : joints) {
        RoboticsJoint identity = robotics_joint_identity(j.axis_id);
        CHECK_Q3("catalog determinant = 1", robotics_circulant_determinant(j), q3(1));
        RoboticsJoint inv = robotics_circulant_inverse(j);
        CHECK("catalog inverse closes", robotics_compose_circulant(j, inv) == identity);
    }

    CHECK("thirds period-6 rotor has period 6",
          robotics_circulant_period(robotics_joint_60()) == 6);
    CHECK("thirds period-2 rotor has period 2",
          robotics_circulant_period(robotics_joint_120()) == 2);
    CHECK("P5 forward bypass has period 3",
          robotics_circulant_period(robotics_joint_p5_forward()) == 3);
    CHECK("P5 inverse is reverse cycle",
          robotics_circulant_inverse(robotics_joint_p5_forward()) == robotics_joint_p5_inverse());
}

static void test_p5_bypass_semantics() {
    RoboticsQuadray v = robotics_sample_vector();
    RoboticsQuadray p5 = robotics_apply_joint(v, robotics_joint_p5_forward());
    RoboticsQuadray recovered = robotics_apply_joint(p5, robotics_joint_p5_inverse());

    CHECK("P5 forward B'=D", p5.b == v.d);
    CHECK("P5 forward C'=B", p5.c == v.b);
    CHECK("P5 forward D'=C", p5.d == v.c);
    CHECK("P5 inverse closes vector", recovered == v);
}

static void test_single_joint_inverse_closure() {
    RoboticsQuadray v0 = robotics_sample_vector();
    RoboticsJoint j = robotics_joint_60(3);
    RoboticsQuadray v1 = robotics_apply_joint(v0, j);
    RoboticsQuadray v2 = robotics_apply_inverse_joint(v1, j);

    CHECK("single joint forward inverse closes", robotics_is_closed(v0, v2));
    CHECK("single joint forward only is not closed", !robotics_is_closed(v0, v1));
}

static void test_fk_inverse_chain_closure() {
    RoboticsQuadray v0 = robotics_sample_vector();
    std::array<RoboticsJoint, 3> joints {
        robotics_joint_60(3),
        robotics_joint_240(1),
        robotics_joint_60(2),
    };

    RoboticsQuadray end = robotics_fk_chain(v0, joints);
    RoboticsQuadray recovered = robotics_inverse_fk_chain(end, joints);

    CHECK("FK chain inverse closes", robotics_is_closed(v0, recovered));
    CHECK("FK chain forward only is not closed", !robotics_is_closed(v0, end));
}

static void test_arc_out_and_back_closure() {
    RoboticsQuadray v0 = robotics_sample_vector();
    RoboticsQuadray out = robotics_pell_step(v0, 12);
    RoboticsQuadray back = robotics_pell_step(out, -12);

    CHECK("Pell arc out and back closes", robotics_is_closed(v0, back));
}

int main() {
    test_pell_inverse_closure();
    test_circulant_inverse_coefficients();
    test_recalculated_rotation_catalog();
    test_p5_bypass_semantics();
    test_single_joint_inverse_closure();
    test_fk_inverse_chain_closure();
    test_arc_out_and_back_closure();

    if (failures == 0) {
        printf("PASS\n");
        return 0;
    }
    printf("FAIL (%d failures)\n", failures);
    return 1;
}
