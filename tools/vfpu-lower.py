#!/usr/bin/env python3
"""vfpu-lower.py <generated unit .cpp>...: rewrite the generic VFPU calls with
literal registers into the compile-time forms of allegrex_context.hpp, in place.

The same rewrites as lower_constant_vfpu_accesses() in profiles/vcs/tools/vcs_codegen_main.cpp
(patch 0012), for units that are not regenerated: running the generator on the
EBOOT gives the same text. Rewrites (all operands literal):
  the vmmul block (two read_vfpu_matrix, the triple loop, write, eat)
                                     -> ctx.vfpu_vmmul_q<D, S, T, N>();
  the prefix-aware vtfm block        -> ctx.vfpu_vtfm_ct<D, M, T, Side, InputLength>();
  ctx.read_vfpu_matrix(x, M, N);     -> ctx.read_vfpu_matrix_ct<M, N>(x);
  ctx.write_vfpu_matrix(x, M, N);    -> ctx.write_vfpu_matrix_ct<M, N>(x);
  ctx.execute_vfpu_<op>(literals);   -> ctx.execute_vfpu_<op>_ct<literals>();
    for cross_quat, vhdp, vx2i, vh2f, vf2h, vocp, vminmax, compare3.
Prints the number of rewrites per kind.
"""
import re
import sys

VMMUL = re.compile(
    r"\{ float vfpu_s\[16\]\{\}, vfpu_t\[16\]\{\}, vfpu_d\[16\]\{\};\n"
    r"\s*ctx\.read_vfpu_matrix\(vfpu_s, ([0-9]+)u, ([1-4])u\);\n"
    r"\s*ctx\.read_vfpu_matrix\(vfpu_t, ([0-9]+)u, \2u\);\n"
    r"\s*for \(std::uint32_t a = 0; a < \2u; \+\+a\) \{\n"
    r"\s*for \(std::uint32_t b = 0; b < \2u; \+\+b\) \{\n"
    r"\s*float sum = 0\.0f;\n"
    r"\s*for \(std::uint32_t c = 0; c < \2u; \+\+c\) sum \+= vfpu_s\[b \* 4u \+ c\] \* vfpu_t\[a \* 4u \+ c\];\n"
    r"\s*vfpu_d\[a \* 4u \+ b\] = sum;\n"
    r"\s*\}\n"
    r"\s*\}\n"
    r"\s*ctx\.write_vfpu_matrix\(vfpu_d, ([0-9]+)u, \2u\);\n"
    r"\s*ctx\.eat_vfpu_prefixes\(\); \}")

# The vtfm block the generator emits where a prefix may be pending (the
# matrix read possibly lowered already).
VTFM = re.compile(
    r"\{ float vfpu_matrix\[16\]\{\}, vfpu_target_raw\[4\]\{\}, vfpu_target\[4\]\{\}, vfpu_result\[4\]\{\};\n"
    r"\s*ctx\.read_vfpu_matrix(?:\(vfpu_matrix, ([0-9]+)u, ([2-4])u\)|_ct<([0-9]+)u, ([2-4])u>\(vfpu_matrix\));\n"
    r"\s*ctx\.read_vfpu_vector_ct<([0-9]+)u, ([2-4])u>\(vfpu_target_raw\);\n"
    r"\s*constexpr std::uint32_t vfpu_side = ([2-4])u;\n"
    r"\s*constexpr std::uint32_t vfpu_input_length = ([1-4])u;\n"
    r"\s*for \(std::uint32_t i = 0; i < 4u; \+\+i\) vfpu_target\[i\] = i < vfpu_input_length \? vfpu_target_raw\[i\] : 0\.0f;\n"
    r"\s*if \(vfpu_side - 1u >= vfpu_input_length\) vfpu_target\[vfpu_side - 1u\] = 1\.0f;\n"
    r"\s*for \(std::uint32_t row = 0; row \+ 1u < vfpu_side; \+\+row\) \{\n"
    r"\s*float sum = 0\.0f;\n"
    r"\s*for \(std::uint32_t column = 0; column < vfpu_side; \+\+column\) sum \+= vfpu_matrix\[row \* 4u \+ column\] \* vfpu_target\[column\];\n"
    r"\s*vfpu_result\[row\] = sum;\n"
    r"\s*\}\n"
    r"\s*float vfpu_final_row\[4\]\{vfpu_matrix\[\(vfpu_side - 1u\) \* 4u \+ 0u\], vfpu_matrix\[\(vfpu_side - 1u\) \* 4u \+ 1u\],\n"
    r"\s*vfpu_matrix\[\(vfpu_side - 1u\) \* 4u \+ 2u\], vfpu_matrix\[\(vfpu_side - 1u\) \* 4u \+ 3u\]\};\n"
    r"\s*ctx\.apply_vfpu_source_prefix(?:_ct<4u, 0u>\(vfpu_final_row\)|\(vfpu_final_row, 4u, 0u\));\n"
    r"\s*ctx\.apply_vfpu_source_prefix(?:_ct<4u, 1u>\(vfpu_target\)|\(vfpu_target, 4u, 1u\));\n"
    r"\s*for \(std::uint32_t column = 0; column < 4u; \+\+column\) vfpu_result\[vfpu_side - 1u\] \+= vfpu_final_row\[column\] \* vfpu_target\[column\];\n"
    r"\s*const std::uint32_t vfpu_destination_prefix = ctx\.vfpu_ctrl\[2\];\n"
    r"\s*const std::uint32_t vfpu_last_lane = vfpu_side - 1u;\n"
    r"\s*ctx\.vfpu_ctrl\[2\] = \(\(vfpu_destination_prefix & \(1u << 8u\)\) << vfpu_last_lane\) \|\n"
    r"\s*\(\(vfpu_destination_prefix & 3u\) << \(vfpu_last_lane \* 2u\)\);\n"
    r"\s*ctx\.write_vfpu_vector_with_destination_prefix\(vfpu_result, ([0-9]+)u, vfpu_side\); \}")


def vtfm_replacement(m):
    matrix = m.group(1) or m.group(3)
    side = m.group(2) or m.group(4)
    if not (side == m.group(6) == m.group(7)):
        return m.group(0)
    return f"ctx.vfpu_vtfm_ct<{m.group(9)}u, {matrix}u, {m.group(5)}u, {side}u, {m.group(8)}u>();"


N = r"([0-9]+)u"
RULES = [
    ("vmmul", VMMUL, r"ctx.vfpu_vmmul_q<\4u, \1u, \3u, \2u>();"),
    ("vtfm", VTFM, vtfm_replacement),
    ("read_matrix", re.compile(r"ctx\.read_vfpu_matrix\(([A-Za-z0-9_]+), " + N + r", ([1-4])u\);"),
     r"ctx.read_vfpu_matrix_ct<\2u, \3u>(\1);"),
    ("write_matrix", re.compile(r"ctx\.write_vfpu_matrix\(([A-Za-z0-9_]+), " + N + r", ([1-4])u\);"),
     r"ctx.write_vfpu_matrix_ct<\2u, \3u>(\1);"),
    ("cross_quat", re.compile(r"ctx\.execute_vfpu_cross_quat\(" + N + ", " + N + ", " + N + r", ([1-4])u\);"),
     r"ctx.execute_vfpu_cross_quat_ct<\1u, \2u, \3u, \4u>();"),
    ("vhdp", re.compile(r"ctx\.execute_vfpu_vhdp\(" + N + ", " + N + ", " + N + r", ([1-4])u\);"),
     r"ctx.execute_vfpu_vhdp_ct<\1u, \2u, \3u, \4u>();"),
    ("vx2i", re.compile(r"ctx\.execute_vfpu_vx2i\(" + N + ", " + N + r", ([1-4])u, ([0-3])u\);"),
     r"ctx.execute_vfpu_vx2i_ct<\1u, \2u, \3u, \4u>();"),
    ("vh2f", re.compile(r"ctx\.execute_vfpu_vh2f\(" + N + ", " + N + r", ([1-4])u\);"),
     r"ctx.execute_vfpu_vh2f_ct<\1u, \2u, \3u>();"),
    ("vf2h", re.compile(r"ctx\.execute_vfpu_vf2h\(" + N + ", " + N + r", ([1-4])u\);"),
     r"ctx.execute_vfpu_vf2h_ct<\1u, \2u, \3u>();"),
    ("vocp", re.compile(r"ctx\.execute_vfpu_vocp\(" + N + ", " + N + r", ([1-4])u\);"),
     r"ctx.execute_vfpu_vocp_ct<\1u, \2u, \3u>();"),
    ("vminmax", re.compile(r"ctx\.execute_vfpu_vminmax\(" + N + ", " + N + ", " + N + r", ([1-4])u, (true|false)\);"),
     r"ctx.execute_vfpu_vminmax_ct<\1u, \2u, \3u, \4u, \5>();"),
    ("compare3", re.compile(r"ctx\.execute_vfpu_compare3\(" + N + ", " + N + ", " + N + r", ([1-4])u, ([5-7])u\);"),
     r"ctx.execute_vfpu_compare3_ct<\1u, \2u, \3u, \4u, \5u>();"),
]


def lower(text, counts):
    for name, pattern, replacement in RULES:
        text, n = pattern.subn(replacement, text)
        counts[name] = counts.get(name, 0) + n
    return text


def main(paths):
    counts = {}
    for path in paths:
        with open(path, newline="") as f:
            text = f.read()
        new = lower(text, counts)
        if new != text:
            with open(path, "w", newline="") as f:
                f.write(new)
    for name, _, _ in RULES:
        print(f"{name:13} {counts.get(name, 0)}")


if __name__ == "__main__":
    main(sys.argv[1:])
