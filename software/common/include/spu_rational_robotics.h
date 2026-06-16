// spu_rational_robotics.h — exact rational robotics simulation oracle
//
// Reconstructs the first public-facing rational robotics layer:
// Pell forward/inverse closure, F/G/H circulant joint inverse closure,
// FK chains, and topological balance checks.
//
// This C++ layer uses exact rational coefficients for simulation and test
// vectors. RTL should use scaled integer constants for the hot paths.

#pragma once

#include <array>
#include <cstdint>
#include <cstdlib>
#include <numeric>

inline int64_t spu_rr_abs64(int64_t x) {
    return x < 0 ? -x : x;
}

struct RationalQ3 {
    int64_t p;
    int64_t q;
    int64_t den;

    RationalQ3(int64_t p_ = 0, int64_t q_ = 0, int64_t den_ = 1)
        : p(p_), q(q_), den(den_) {
        normalize();
    }

    void normalize() {
        if (den < 0) {
            den = -den;
            p = -p;
            q = -q;
        }
        int64_t g = std::gcd(spu_rr_abs64(p), spu_rr_abs64(q));
        g = std::gcd(g, spu_rr_abs64(den));
        if (g == 0)
            g = 1;
        p /= g;
        q /= g;
        den /= g;
    }

    bool is_zero() const {
        return p == 0 && q == 0;
    }

    RationalQ3 operator+(const RationalQ3& o) const {
        return RationalQ3(p * o.den + o.p * den,
                          q * o.den + o.q * den,
                          den * o.den);
    }

    RationalQ3 operator-(const RationalQ3& o) const {
        return RationalQ3(p * o.den - o.p * den,
                          q * o.den - o.q * den,
                          den * o.den);
    }

    RationalQ3 operator-() const {
        return RationalQ3(-p, -q, den);
    }

    RationalQ3 operator*(const RationalQ3& o) const {
        return RationalQ3(
            p * o.p + 3 * q * o.q,
            p * o.q + q * o.p,
            den * o.den);
    }

    bool operator==(const RationalQ3& o) const {
        return p == o.p && q == o.q && den == o.den;
    }

    bool operator!=(const RationalQ3& o) const {
        return !(*this == o);
    }

    RationalQ3 square() const {
        return *this * *this;
    }

    RationalQ3 conjugate() const {
        return RationalQ3(p, -q, den);
    }
};

inline RationalQ3 q3(int64_t p, int64_t q = 0, int64_t den = 1) {
    return RationalQ3(p, q, den);
}

constexpr int SPU_RR_AXES = 4;

struct RoboticsQuadray {
    RationalQ3 a, b, c, d;

    std::array<RationalQ3, SPU_RR_AXES> components() const {
        return { a, b, c, d };
    }

    bool operator==(const RoboticsQuadray& o) const {
        return a == o.a && b == o.b && c == o.c && d == o.d;
    }

    bool operator!=(const RoboticsQuadray& o) const {
        return !(*this == o);
    }

    RoboticsQuadray operator+(const RoboticsQuadray& o) const {
        return { a + o.a, b + o.b, c + o.c, d + o.d };
    }

    RoboticsQuadray operator-(const RoboticsQuadray& o) const {
        return { a - o.a, b - o.b, c - o.c, d - o.d };
    }

    RoboticsQuadray scale(const RationalQ3& s) const {
        return { a * s, b * s, c * s, d * s };
    }

    bool is_zero() const {
        return a.is_zero() && b.is_zero() && c.is_zero() && d.is_zero();
    }

    RationalQ3 quadrance() const {
        auto comps = components();
        RationalQ3 total;
        for (int i = 0; i < SPU_RR_AXES; i++) {
            for (int j = i + 1; j < SPU_RR_AXES; j++) {
                RationalQ3 diff = comps[i] - comps[j];
                total = total + diff.square();
            }
        }
        return total;
    }

    RoboticsQuadray circulant_rotate(const RationalQ3& f,
                                     const RationalQ3& g,
                                     const RationalQ3& h) const {
        RationalQ3 b2 = f * b + h * c + g * d;
        RationalQ3 c2 = g * b + f * c + h * d;
        RationalQ3 d2 = h * b + g * c + f * d;
        return { a, b2, c2, d2 };
    }
};

struct RoboticsJoint {
    int axis_id;
    RationalQ3 f, g, h;

    bool operator==(const RoboticsJoint& o) const {
        return axis_id == o.axis_id && f == o.f && g == o.g && h == o.h;
    }
};

struct RoboticsSixStepFrame {
    int phase;
    int forward_angle;
    int inverse_angle;
    RoboticsQuadray input_vector;
    RoboticsQuadray commanded_vector;
    RoboticsQuadray recovered_vector;
    RoboticsQuadray closure_error_vector;
    RationalQ3 quadrance_before;
    RationalQ3 quadrance_after;
    bool inverse_balanced;
    bool orbit_closed;
};

inline RoboticsJoint robotics_joint_identity(int axis_id = 0) {
    return { axis_id, q3(1), q3(0), q3(0) };
}

inline RoboticsJoint robotics_joint_60(int axis_id = 3) {
    return { axis_id, q3(2, 0, 3), q3(2, 0, 3), q3(-1, 0, 3) };
}

inline RoboticsJoint robotics_joint_120(int axis_id = 3) {
    return { axis_id, q3(-1, 0, 3), q3(2, 0, 3), q3(2, 0, 3) };
}

inline RoboticsJoint robotics_joint_240(int axis_id = 3) {
    return { axis_id, q3(2, 0, 3), q3(-1, 0, 3), q3(2, 0, 3) };
}

inline RoboticsJoint robotics_joint_p5_forward(int axis_id = 3) {
    return { axis_id, q3(0), q3(1), q3(0) };
}

inline RoboticsJoint robotics_joint_p5_inverse(int axis_id = 3) {
    return { axis_id, q3(0), q3(0), q3(1) };
}

inline RationalQ3 robotics_circulant_determinant(const RoboticsJoint& j) {
    return j.f * j.f * j.f
         + j.g * j.g * j.g
         + j.h * j.h * j.h
         - q3(3) * j.f * j.g * j.h;
}

inline RoboticsJoint robotics_compose_circulant(const RoboticsJoint& first,
                                                const RoboticsJoint& second) {
    return {
        first.axis_id,
        first.f * second.f + first.h * second.g + first.g * second.h,
        first.g * second.f + first.f * second.g + first.h * second.h,
        first.h * second.f + first.g * second.g + first.f * second.h,
    };
}

inline RoboticsJoint robotics_circulant_inverse(const RoboticsJoint& j) {
    return {
        j.axis_id,
        j.f * j.f - j.g * j.h,
        j.h * j.h - j.f * j.g,
        j.g * j.g - j.f * j.h,
    };
}

inline RoboticsQuadray robotics_apply_joint(const RoboticsQuadray& v,
                                            const RoboticsJoint& j) {
    return v.circulant_rotate(j.f, j.g, j.h);
}

inline RoboticsQuadray robotics_apply_inverse_joint(const RoboticsQuadray& v,
                                                    const RoboticsJoint& j) {
    return robotics_apply_joint(v, robotics_circulant_inverse(j));
}

template <std::size_t N>
inline RoboticsQuadray robotics_fk_chain(
    const RoboticsQuadray& base,
    const std::array<RoboticsJoint, N>& joints
) {
    RoboticsQuadray v = base;
    for (const auto& joint : joints)
        v = robotics_apply_joint(v, joint);
    return v;
}

template <std::size_t N>
inline RoboticsQuadray robotics_inverse_fk_chain(
    const RoboticsQuadray& end_effector,
    const std::array<RoboticsJoint, N>& joints
) {
    RoboticsQuadray v = end_effector;
    for (std::size_t i = N; i > 0; i--)
        v = robotics_apply_inverse_joint(v, joints[i - 1]);
    return v;
}

inline RoboticsQuadray robotics_pell_step(const RoboticsQuadray& v, int steps) {
    RationalQ3 scalar = q3(1);
    RationalQ3 rotor = steps >= 0 ? q3(2, 1) : q3(2, -1);
    int n = steps >= 0 ? steps : -steps;
    for (int i = 0; i < n; i++)
        scalar = scalar * rotor;
    return v.scale(scalar);
}

inline RoboticsQuadray robotics_closure_error(const RoboticsQuadray& start,
                                              const RoboticsQuadray& recovered) {
    return recovered - start;
}

inline bool robotics_is_closed(const RoboticsQuadray& start,
                               const RoboticsQuadray& recovered) {
    return robotics_closure_error(start, recovered).is_zero();
}

inline int robotics_circulant_period(const RoboticsJoint& j, int max_steps = 12) {
    RoboticsJoint identity = robotics_joint_identity(j.axis_id);
    RoboticsJoint current = identity;
    for (int n = 1; n <= max_steps; n++) {
        current = robotics_compose_circulant(j, current);
        if (current == identity)
            return n;
    }
    return 0;
}

inline RoboticsQuadray robotics_sample_vector() {
    return { q3(1), q3(0, 1), q3(1, 0, 3), q3(-2) };
}

inline RoboticsJoint robotics_corrected_rotc_joint(int angle) {
    switch (angle) {
    case 0: return robotics_joint_identity();
    case 1: return robotics_joint_60();
    case 2: return robotics_joint_p5_forward();
    case 3: return robotics_joint_120();
    case 4: return robotics_joint_240();
    case 5: return robotics_joint_p5_inverse();
    default: return robotics_joint_identity();
    }
}

inline int robotics_inverse_angle_for(int angle) {
    switch (angle) {
    case 0: return 0;
    case 1: return 4;
    case 2: return 5;
    case 3: return 3;
    case 4: return 1;
    case 5: return 2;
    default: return -1;
    }
}

inline std::array<RoboticsSixStepFrame, 6> robotics_six_step_trace(
    const RoboticsQuadray& start,
    int angle = 1
) {
    std::array<RoboticsSixStepFrame, 6> trace {};
    RoboticsQuadray root = start;
    RoboticsQuadray current = start;
    RoboticsJoint forward_joint = robotics_corrected_rotc_joint(angle);
    int inverse_angle = robotics_inverse_angle_for(angle);
    RoboticsJoint inverse_joint = robotics_corrected_rotc_joint(inverse_angle);

    for (int phase = 0; phase < 6; phase++) {
        RoboticsQuadray commanded = robotics_apply_joint(current, forward_joint);
        RoboticsQuadray recovered = robotics_apply_joint(commanded, inverse_joint);
        RoboticsQuadray error = robotics_closure_error(current, recovered);
        trace[phase] = {
            phase,
            angle,
            inverse_angle,
            current,
            commanded,
            recovered,
            error,
            current.quadrance(),
            commanded.quadrance(),
            error.is_zero(),
            robotics_is_closed(root, commanded),
        };
        current = commanded;
    }

    return trace;
}

inline std::array<RoboticsSixStepFrame, 6> robotics_six_step_trace(int angle = 1) {
    return robotics_six_step_trace(robotics_sample_vector(), angle);
}

inline bool robotics_six_step_trace_is_balanced(
    const std::array<RoboticsSixStepFrame, 6>& trace
) {
    for (const auto& frame : trace) {
        if (!frame.inverse_balanced)
            return false;
    }
    return trace[5].orbit_closed;
}
