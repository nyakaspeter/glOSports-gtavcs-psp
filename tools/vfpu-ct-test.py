#!/usr/bin/env python3
"""vfpu-ct-test.py [units dir] [header dir]: check the compile-time VFPU forms
(patch 0012, LCS 0042) against the generic ones, bit for bit, natively in the builder
image (AArch64 NEON is IEEE where the console's ARMv7 NEON flushes subnormals
to zero, as every NEON form since patch 0036 does).

Every register combination the generated units use (after tools/vfpu-lower.py)
is instantiated, plus random ones; each runs on random register files with
zeros of both signs, infinities, NaNs with payloads, subnormals and ordinary
numbers, with the default prefixes (the fast path) and with random pending
prefixes (the generic fallback). The plain write behind a zero destination
prefix is checked against a copy of the old writer.
"""
import os
import random
import re
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
units = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "upstream", "profiles", "vcs", "generated")
include = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "upstream", "include")
image = os.environ.get("IMAGE", "vcs-recomp-builder")

forms = {
    "cross_quat": (r"execute_vfpu_cross_quat_ct<(\d+)u, (\d+)u, (\d+)u, (\d)u>", 4),
    "vhdp": (r"execute_vfpu_vhdp_ct<(\d+)u, (\d+)u, (\d+)u, (\d)u>", 4),
    "vx2i": (r"execute_vfpu_vx2i_ct<(\d+)u, (\d+)u, (\d)u, (\d)u>", 4),
    "vh2f": (r"execute_vfpu_vh2f_ct<(\d+)u, (\d+)u, (\d)u>", 3),
    "vf2h": (r"execute_vfpu_vf2h_ct<(\d+)u, (\d+)u, (\d)u>", 3),
    "vocp": (r"execute_vfpu_vocp_ct<(\d+)u, (\d+)u, (\d)u>", 3),
    "vminmax": (r"execute_vfpu_vminmax_ct<(\d+)u, (\d+)u, (\d+)u, (\d)u, (true|false)>", 5),
    "compare3": (r"execute_vfpu_compare3_ct<(\d+)u, (\d+)u, (\d+)u, (\d)u, (\d)u>", 5),
    "vmmul": (r"vfpu_vmmul_q<(\d+)u, (\d+)u, (\d+)u, (\d)u>", 4),
    "vtfm": (r"vfpu_vtfm_ct<(\d+)u, (\d+)u, (\d+)u, (\d)u, (\d)u>", 5),
    "read_matrix": (r"read_vfpu_matrix_ct<(\d+)u, (\d)u>", 2),
    "write_matrix": (r"write_vfpu_matrix_ct<(\d+)u, (\d)u>", 2),
    "dprefix": (r"write_vfpu_vector_with_destination_prefix_ct<(\d+)u, (\d)u>", 2),
}
seen = {k: set() for k in forms}
for name in sorted(os.listdir(units)):
    if not name.startswith("generated_unit_"):
        continue
    text = open(os.path.join(units, name)).read()
    for k, (pattern, _) in forms.items():
        for m in re.finditer(pattern, text):
            seen[k].add(m.groups())

rng = random.Random(42)
def reg(): return rng.randrange(128)
for _ in range(40):  # random combinations beyond the ones in use
    seen["cross_quat"].add((str(reg()), str(reg()), str(reg()), str(rng.choice([3, 4]))))
    seen["vhdp"].add((str(reg()), str(reg()), str(reg()), str(rng.randint(1, 4))))
    seen["vx2i"].add((str(reg()), str(reg()), str(rng.randint(1, 4)), str(rng.randint(0, 3))))
    seen["vh2f"].add((str(reg()), str(reg()), str(rng.randint(1, 4))))
    seen["vf2h"].add((str(reg()), str(reg()), str(rng.randint(1, 4))))
    seen["vocp"].add((str(reg()), str(reg()), str(rng.randint(1, 4))))
    seen["vminmax"].add((str(reg()), str(reg()), str(reg()), str(rng.randint(1, 4)), rng.choice(["true", "false"])))
    seen["compare3"].add((str(reg()), str(reg()), str(reg()), str(rng.randint(1, 4)), str(rng.randint(5, 7))))
    seen["vmmul"].add((str(reg()), str(reg()), str(reg()), str(rng.randint(1, 4))))
    side = rng.randint(2, 4)
    seen["vtfm"].add((str(reg()), str(reg()), str(reg()), str(side), str(rng.randint(1, side))))
    seen["read_matrix"].add((str(reg()), str(rng.randint(1, 4))))
    seen["write_matrix"].add((str(reg()), str(rng.randint(1, 4))))
    seen["dprefix"].add((str(reg()), str(rng.randint(1, 4))))

calls = []
def add(kind, generic, ct, prefixed_ok=True):
    calls.append((kind, generic, ct, prefixed_ok))

for d, s, t, l in sorted(seen["cross_quat"]):
    add("cross_quat", f"c.execute_vfpu_cross_quat({d}u, {s}u, {t}u, {l}u);", f"c.execute_vfpu_cross_quat_ct<{d}u, {s}u, {t}u, {l}u>();")
for d, s, t, l in sorted(seen["vhdp"]):
    add("vhdp", f"c.execute_vfpu_vhdp({d}u, {s}u, {t}u, {l}u);", f"c.execute_vfpu_vhdp_ct<{d}u, {s}u, {t}u, {l}u>();")
for d, s, l, op in sorted(seen["vx2i"]):
    add("vx2i", f"c.execute_vfpu_vx2i({d}u, {s}u, {l}u, {op}u);", f"c.execute_vfpu_vx2i_ct<{d}u, {s}u, {l}u, {op}u>();")
for d, s, l in sorted(seen["vh2f"]):
    add("vh2f", f"c.execute_vfpu_vh2f({d}u, {s}u, {l}u);", f"c.execute_vfpu_vh2f_ct<{d}u, {s}u, {l}u>();")
for d, s, l in sorted(seen["vf2h"]):
    add("vf2h", f"c.execute_vfpu_vf2h({d}u, {s}u, {l}u);", f"c.execute_vfpu_vf2h_ct<{d}u, {s}u, {l}u>();")
for d, s, l in sorted(seen["vocp"]):
    add("vocp", f"c.execute_vfpu_vocp({d}u, {s}u, {l}u);", f"c.execute_vfpu_vocp_ct<{d}u, {s}u, {l}u>();")
for d, s, t, l, mx in sorted(seen["vminmax"]):
    add("vminmax", f"c.execute_vfpu_vminmax({d}u, {s}u, {t}u, {l}u, {mx});", f"c.execute_vfpu_vminmax_ct<{d}u, {s}u, {t}u, {l}u, {mx}>();")
for d, s, t, l, op in sorted(seen["compare3"]):
    add("compare3", f"c.execute_vfpu_compare3({d}u, {s}u, {t}u, {l}u, {op}u);", f"c.execute_vfpu_compare3_ct<{d}u, {s}u, {t}u, {l}u, {op}u>();")
for d, s, t, n in sorted(seen["vmmul"]):
    add("vmmul", f"ref_vmmul(c, {d}u, {s}u, {t}u, {n}u);", f"c.vfpu_vmmul_q<{d}u, {s}u, {t}u, {n}u>();")
for d, m, t, side, inl in sorted(seen["vtfm"]):
    add("vtfm", f"ref_vtfm(c, {d}u, {m}u, {t}u, {side}u, {inl}u);", f"c.vfpu_vtfm_ct<{d}u, {m}u, {t}u, {side}u, {inl}u>();")
for m, n in sorted(seen["read_matrix"]):
    add("read_matrix", f"{{ float x[16]{{}}; c.read_vfpu_matrix(x, {m}u, {n}u); sink(c, x); }}",
        f"{{ float x[16]{{}}; c.read_vfpu_matrix_ct<{m}u, {n}u>(x); sink(c, x); }}")
for m, n in sorted(seen["write_matrix"]):
    add("write_matrix", f"{{ float x[16]; source16(x); c.write_vfpu_matrix(x, {m}u, {n}u); }}",
        f"{{ float x[16]; source16(x); c.write_vfpu_matrix_ct<{m}u, {n}u>(x); }}")
for r, n in sorted(seen["dprefix"]):
    add("dprefix", f"{{ float x[4]; source4(x); old_write_dest_prefix(c, x, {r}u, {n}u); }}",
        f"{{ float x[4]; source4(x); c.write_vfpu_vector_with_destination_prefix_ct<{r}u, {n}u>(x); }}")
    add("dprefix_generic", f"{{ float x[4]; source4(x); old_write_dest_prefix(c, x, {r}u, {n}u); }}",
        f"{{ float x[4]; source4(x); c.write_vfpu_vector_with_destination_prefix(x, {r}u, {n}u); }}")

src = [r'''#include "psprecomp/allegrex_context.hpp"
#include <cstdio>
#include <cstring>
#include <random>
using psprecomp::AllegrexContext;
static std::mt19937 rng(1234);
static std::uint32_t pool_bits() {
    static const std::uint32_t special[] = {0x00000000u, 0x80000000u, 0x3F800000u, 0xBF800000u, 0x3F000000u,
        0x40000000u, 0x7F800000u, 0xFF800000u, 0x7FC00000u, 0xFFC00001u, 0x7F800001u, 0x7FBFFFFFu,
        0x00000001u, 0x807FFFFFu, 0x00400000u, 0x7F7FFFFFu, 0xFF7FFFFFu, 0x33800000u, 0x477FE000u,
        0x387FC000u, 0x0000FFFFu, 0xFFFF0000u, 0x12345678u, 0x80008000u};
    switch (rng() % 4u) {
    case 0: return special[rng() % (sizeof(special) / sizeof(special[0]))];
    case 1: return rng();
    default: { std::uniform_real_distribution<float> d(-100.0f, 100.0f); float f = d(rng); std::uint32_t b; std::memcpy(&b, &f, 4); return b; }
    }
}
static float pool() { const std::uint32_t b = pool_bits(); float f; std::memcpy(&f, &b, 4); return f; }
static void randomize(AllegrexContext &c, bool prefixed) {
    for (auto &v : c.vfpu) v = pool();
    for (auto &w : c.vfpu_ctrl) w = rng();
    c.vfpu_ctrl[0] = 0xE4u; c.vfpu_ctrl[1] = 0xE4u; c.vfpu_ctrl[2] = 0u;
    if (prefixed) {
        switch (rng() % 4u) {
        case 0: c.vfpu_ctrl[0] = rng() & 0x000FFFFFu; break;
        case 1: c.vfpu_ctrl[1] = rng() & 0x000FFFFFu; break;
        case 2: c.vfpu_ctrl[2] = rng() & 0x00000FFFu; break;
        default: c.vfpu_ctrl[0] = rng() & 0x000FFFFFu; c.vfpu_ctrl[1] = rng() & 0x000FFFFFu;
                 c.vfpu_ctrl[2] = rng() & 0x00000FFFu; break;
        }
    }
}
static float sink_values[16];
static void sink(AllegrexContext &c, const float *x) { std::memcpy(c.fpr.data(), x, 16 * sizeof(float)); }
static std::uint32_t source_seed;
static void source16(float *x) { std::mt19937 r(source_seed); for (int i = 0; i < 16; ++i) { std::uint32_t b = r(); std::memcpy(&x[i], &b, 4); } }
static void source4(float *x) { std::mt19937 r(source_seed); for (int i = 0; i < 4; ++i) { std::uint32_t b = r() % 3u ? r() : 0x3F800000u; std::memcpy(&x[i], &b, 4); } }
// The generator's vmmul block, as emitted before patch 0042.
static void ref_vmmul(AllegrexContext &ctx, std::uint32_t d, std::uint32_t s, std::uint32_t t, std::uint32_t n) {
    float vfpu_s[16]{}, vfpu_t[16]{}, vfpu_d[16]{};
    ctx.read_vfpu_matrix(vfpu_s, s, n);
    ctx.read_vfpu_matrix(vfpu_t, t, n);
    for (std::uint32_t a = 0; a < n; ++a) {
        for (std::uint32_t b = 0; b < n; ++b) {
            float sum = 0.0f;
            for (std::uint32_t c = 0; c < n; ++c) sum += vfpu_s[b * 4u + c] * vfpu_t[a * 4u + c];
            vfpu_d[a * 4u + b] = sum;
        }
    }
    ctx.write_vfpu_matrix(vfpu_d, d, n);
    ctx.eat_vfpu_prefixes();
}
// write_vfpu_vector_with_destination_prefix before patch 0042.
static void old_write_dest_prefix(AllegrexContext &c, const float *source, std::uint32_t vector_register, std::uint32_t length) {
    float value[4]{};
    const std::uint32_t destination_prefix = c.vfpu_ctrl[2];
    for (std::uint32_t i = 0; i < length && i < 4u; ++i) {
        value[i] = source[i];
        const std::uint32_t saturation = (destination_prefix >> (i * 2u)) & 3u;
        if (saturation == 1u) value[i] = std::fmin(1.0f, std::fmax(0.0f, value[i]));
        else if (saturation == 3u) value[i] = std::fmin(1.0f, std::fmax(-1.0f, value[i]));
    }
    const std::uint32_t row = length == 3u ? ((vector_register >> 6u) & 1u) : ((vector_register >> 5u) & 2u);
    const bool transpose = ((vector_register >> 5u) & 1u) != 0u;
    const std::uint32_t matrix_base = ((vector_register << 2u) & 0x70u);
    const std::uint32_t column = vector_register & 3u;
    for (std::uint32_t i = 0; i < length && i < 4u; ++i) {
        if (((destination_prefix >> (8u + i)) & 1u) != 0u) continue;
        const std::size_t index = length == 1u ? AllegrexContext::vfpu_scalar_index(vector_register & 0x7Fu)
            : (transpose ? static_cast<std::size_t>(matrix_base + column + ((row + i) & 3u) * 4u)
                         : static_cast<std::size_t>(matrix_base + column * 4u + ((row + i) & 3u)));
        c.vfpu[index] = value[i];
    }
    c.eat_vfpu_prefixes();
}
// The generator's prefix-aware vtfm block (as in the VCS units), literally.
static void ref_vtfm(AllegrexContext &ctx, std::uint32_t d, std::uint32_t m, std::uint32_t t,
                     std::uint32_t side, std::uint32_t input_length) {
    float vfpu_matrix[16]{}, vfpu_target_raw[4]{}, vfpu_target[4]{}, vfpu_result[4]{};
    ctx.read_vfpu_matrix(vfpu_matrix, m, side);
    ctx.read_vfpu_vector(vfpu_target_raw, t, side);
    const std::uint32_t vfpu_side = side;
    const std::uint32_t vfpu_input_length = input_length;
    for (std::uint32_t i = 0; i < 4u; ++i) vfpu_target[i] = i < vfpu_input_length ? vfpu_target_raw[i] : 0.0f;
    if (vfpu_side - 1u >= vfpu_input_length) vfpu_target[vfpu_side - 1u] = 1.0f;
    for (std::uint32_t row = 0; row + 1u < vfpu_side; ++row) {
      float sum = 0.0f;
      for (std::uint32_t column = 0; column < vfpu_side; ++column) sum += vfpu_matrix[row * 4u + column] * vfpu_target[column];
      vfpu_result[row] = sum;
    }
    float vfpu_final_row[4]{vfpu_matrix[(vfpu_side - 1u) * 4u + 0u], vfpu_matrix[(vfpu_side - 1u) * 4u + 1u],
                            vfpu_matrix[(vfpu_side - 1u) * 4u + 2u], vfpu_matrix[(vfpu_side - 1u) * 4u + 3u]};
    ctx.apply_vfpu_source_prefix(vfpu_final_row, 4u, 0u);
    ctx.apply_vfpu_source_prefix(vfpu_target, 4u, 1u);
    for (std::uint32_t column = 0; column < 4u; ++column) vfpu_result[vfpu_side - 1u] += vfpu_final_row[column] * vfpu_target[column];
    const std::uint32_t vfpu_destination_prefix = ctx.vfpu_ctrl[2];
    const std::uint32_t vfpu_last_lane = vfpu_side - 1u;
    ctx.vfpu_ctrl[2] = ((vfpu_destination_prefix & (1u << 8u)) << vfpu_last_lane) |
                       ((vfpu_destination_prefix & 3u) << (vfpu_last_lane * 2u));
    old_write_dest_prefix(ctx, vfpu_result, d, vfpu_side);
}
static int failures = 0;
static long checks = 0;
static long nan_payloads = 0;
// Equal bits, except that a NaN equals any NaN: which operand's payload a NaN
// result carries depends on the order the compiler gives a commutative
// operation, in either form (and the PSP's own NaNs are neither).
static bool same(const AllegrexContext &a, const AllegrexContext &b) {
    bool payload_only = false;
    auto same_float = [&](float x, float y) {
        std::uint32_t p, q; std::memcpy(&p, &x, 4); std::memcpy(&q, &y, 4);
        if (p == q) return true;
        if (std::isnan(x) && std::isnan(y)) { payload_only = true; return true; }
        return false;
    };
    for (std::size_t i = 0; i < a.vfpu.size(); ++i) if (!same_float(a.vfpu[i], b.vfpu[i])) return false;
    for (std::size_t i = 0; i < a.fpr.size(); ++i) if (!same_float(a.fpr[i], b.fpr[i])) return false;
    if (a.vfpu_ctrl != b.vfpu_ctrl || a.gpr != b.gpr || a.pc != b.pc || a.hi != b.hi || a.lo != b.lo || a.fcr31 != b.fcr31)
        return false;
    if (payload_only) ++nan_payloads;
    return true;
}
template <class G, class F>
static void check(const char *kind, int site, G generic, F ct) {
    for (int round = 0; round < 400; ++round) {
        const bool prefixed = round % 4 == 3;
        AllegrexContext a{};
        randomize(a, prefixed);
        AllegrexContext b = a;
        source_seed = static_cast<std::uint32_t>(rng());
        generic(a);
        ct(b);
        ++checks;
        if (!same(a, b)) {
            if (++failures <= 20) {
                std::printf("MISMATCH %s site %d round %d prefixed=%d\n", kind, site, round, prefixed ? 1 : 0);
                for (std::size_t i = 0; i < a.vfpu.size(); ++i) {
                    std::uint32_t x, y; std::memcpy(&x, &a.vfpu[i], 4); std::memcpy(&y, &b.vfpu[i], 4);
                    if (x != y) std::printf("  vfpu[%zu] generic %08x ct %08x\n", i, x, y);
                }
                for (std::size_t i = 0; i < a.vfpu_ctrl.size(); ++i)
                    if (a.vfpu_ctrl[i] != b.vfpu_ctrl[i]) std::printf("  ctrl[%zu] generic %08x ct %08x\n", i, a.vfpu_ctrl[i], b.vfpu_ctrl[i]);
            }
        }
    }
}
int main() {
''']
for i, (kind, generic, ct, _) in enumerate(calls):
    src.append(f'    check("{kind}", {i}, [](AllegrexContext &c) {{ {generic} }}, [](AllegrexContext &c) {{ {ct} }});\n')
src.append(r'''    std::printf("%ld checks, %d mismatches, %ld with NaN payloads differing\n", checks, failures, nan_payloads);
    return failures != 0;
}
''')
out_dir = os.path.join(here, "..", "build", "vfpu-ct-test")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "vfpu_ct_test.cpp"), "w") as f:
    f.write("".join(src))
print(f"{len(calls)} sites: " + ", ".join(f"{k} {len(v)}" for k, v in seen.items()))
root = os.path.abspath(os.path.join(here, ".."))
inc = os.path.abspath(include)
cmd = ["docker", "run", "--rm", "-v", f"{root}:/w", "-v", f"{inc}:/inc", "-w", "/w/build/vfpu-ct-test", image, "sh", "-c",
       "g++ -std=c++20 -O2 -ffp-contract=off -fno-strict-aliasing -I/inc -o vfpu_ct_test vfpu_ct_test.cpp && ./vfpu_ct_test"]
sys.exit(subprocess.call(cmd))
