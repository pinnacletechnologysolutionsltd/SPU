#ifndef SPU_CHECKED_MATH_H
#define SPU_CHECKED_MATH_H
#include <cstdint>
#include <climits>
#include <stdexcept>
#include <string>
#include <algorithm>

// Software-only bounded backend: widen before computing, check before commit.
using Wide = __int128;
struct VmFault : std::runtime_error {
    std::string kind;
    VmFault(const std::string& k, const std::string& message)
        : std::runtime_error(message), kind(k) {}
};
static int32_t checked_i32(Wide value) {
    if (value < INT32_MIN || value > INT32_MAX)
        throw VmFault("OVERFLOW", "signed32 coefficient overflow");
    return static_cast<int32_t>(value);
}
static Wide nearest_div(Wide value, int32_t denominator) {
    Wide magnitude = value < 0 ? -value : value;
    Wide quotient = (magnitude + denominator / 2) / denominator;
    return value < 0 ? -quotient : quotient;
}
static std::string wide_string(Wide value) {
    if (value == 0) return "0";
    bool negative = value < 0;
    if (negative) value = -value;
    std::string out;
    while (value) {
        out.push_back('0' + value % 10);
        value /= 10;
    }
    if (negative) out.push_back('-');
    std::reverse(out.begin(), out.end());
    return out;
}
#endif
