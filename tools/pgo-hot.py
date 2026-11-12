#!/usr/bin/env python3
"""pgo-hot.py [count] [name part]: rank functions by the committed PGO profile (pgo/*.gcda),
the counters the instrumented build collected on the console in tools/pgo.sh's
run (the opening cutscene, the barracks, 90 s along a busy street): a profile without the
console.

The arc counters of a function sum to about the number of its basic blocks run,
so out-of-line helpers that loop over a few lanes look bigger than their share
of the time; the max column (the busiest arc) is the call count of a function
without loops. A gcda names a function by the CRC GCC computes from its mangled
name (coverage_compute_profile_id): externally visible functions are matched
against the symbols of the build's objects, static ones stay "?".

With a name part (recomp_leaf_, recomp_fn_, recomp_unit_) only those functions,
by their busiest arc.

Needs a build in build/ (the objects for the names) and the builder image.
"""
import collections
import os
import re
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, ".."))
image = os.environ.get("IMAGE", "vcs-recomp-builder")
count = int(sys.argv[1]) if len(sys.argv) > 1 else 60

script = r'''
for f in pgo/*.gcda; do gcov-dump -l "$f"; done > /tmp/gcda.txt 2>&1
for f in $(find build -name '*.o'); do arm-linux-gnueabihf-nm --defined-only "$f" 2>/dev/null; done > /tmp/nm.txt
cat /tmp/gcda.txt; echo '=====NM====='; cat /tmp/nm.txt
'''
out = subprocess.run(["docker", "run", "--rm", "-v", f"{root}:/w", "-w", "/w", image, "sh", "-c", script],
                     capture_output=True, text=True, check=True).stdout
gcda, nm = out.split("=====NM=====\n", 1)


def crc32_string(chk, s):  # gcc/crc32.cc, the terminating NUL included
    for ch in s.encode() + b"\0":
        value = ch << 24
        for _ in range(8):
            feedback = 0x04C11DB7 if (value ^ chk) & 0x80000000 else 0
            chk = ((chk << 1) & 0xFFFFFFFF) ^ feedback
            value = (value << 1) & 0xFFFFFFFF
    return chk


names = {}
for line in nm.splitlines():
    parts = line.split()
    if len(parts) == 3 and parts[1] in "TW":
        c = crc32_string(0, parts[2]) & 0x7FFFFFFF
        names[c + (c == 0)] = parts[2]

total = collections.Counter()
busiest = collections.Counter()
current = None
mode = None
for line in gcda.splitlines():
    m = re.search(r"(\S+\.gcda):\s+01000000:\s+\d+:FUNCTION ident=(\d+)", line)
    if m:
        current = (m.group(1).split("#")[-1].replace(".gcda", ""), int(m.group(2)))
        mode = None
        continue
    if "COUNTERS arcs" in line:
        mode = "arcs"
        continue
    if "COUNTERS" in line:
        mode = None
        continue
    m = re.match(r".*gcda:\s+\d+: ([\d ]+)$", line)
    if m and current and mode == "arcs":
        values = [int(x) for x in m.group(1).split()]
        total[current] += sum(values)
        busiest[current] = max(busiest[current], max(values))

grand = sum(total.values())
# By kind of generated code, and how often the leaf functions are called
# (a leaf has no loop to speak of: its busiest arc is its call count).
kinds = collections.Counter()
calls = collections.Counter()
for (unit, ident), value in total.items():
    name = names.get(ident, "?")
    kind = ("leaf functions" if "recomp_leaf_" in name else "call functions" if "recomp_fn_" in name
            else "unit bodies" if "recomp_unit_" in name else "host code")
    kinds[kind] += value
    calls[kind] += busiest[(unit, ident)]
for kind, value in kinds.most_common():
    print(f"{100 * value / grand:5.1f}% of the arc counts in {kind}; busiest arcs summed {calls[kind]:,}")
mode = sys.argv[2] if len(sys.argv) > 2 else ""
ranked = total.most_common() if not mode else sorted(
    ((key, value) for key, value in total.items() if mode in names.get(key[1], "?")),
    key=lambda item: -busiest[item[0]])
wanted = [names.get(i, "?") for (_, i), _ in ranked[:count]]
plain = subprocess.run(["c++filt"], input="\n".join(wanted), capture_output=True, text=True).stdout.splitlines()
demangled = dict(zip(wanted, plain))
print(f"{'share':>6} {'busiest arc':>12}  file / function")
for (unit, ident), value in ranked[:count]:
    name = names.get(ident, "?")
    print(f"{100 * value / grand:5.2f}% {busiest[(unit, ident)]:12}  {unit}  {demangled.get(name, name)[:110]}")
