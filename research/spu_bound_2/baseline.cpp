// Small, bounded denominator-one comparison. Not a Gen-1 simulator.
#include <chrono>
#include <cstdint>
#include <cstdio>
struct Pair { std::int64_t a,b; };
extern "C" __attribute__((noinline)) Pair eager(Pair x) {
    Pair t{2*x.a+3*x.b, x.a+2*x.b};
    return {2*t.a-3*t.b, -t.a+2*t.b};
}
extern "C" __attribute__((noinline)) Pair algebraic(Pair x) { return x; }
volatile std::int64_t sink;
int main() {
    constexpr int n=1000000;
    for (int a=-2;a<=2;a++) for(int b=-2;b<=2;b++) {
        Pair x{a,b}, y=eager(x), z=algebraic(x);
        if (y.a != x.a || y.b != x.b || z.a != x.a || z.b != x.b) return 1;
    }
    for (int mode=0;mode<2;mode++) {
        std::int64_t sum=0;
        auto start=std::chrono::steady_clock::now();
        for(int i=0;i<n;i++) {
            Pair x{(i%5)-2, ((i/5)%5)-2};
            Pair y=mode ? algebraic(x) : eager(x);
            sum+=y.a+3*y.b;
        }
        auto end=std::chrono::steady_clock::now();
        sink=sum;
        std::printf("%s n=%d sum=%lld ns=%lld\n",mode?"algebraic":"eager",n,
          static_cast<long long>(sum),static_cast<long long>(std::chrono::duration_cast<std::chrono::nanoseconds>(end-start).count()));
    }
}
