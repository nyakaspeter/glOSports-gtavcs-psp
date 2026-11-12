#!/usr/bin/env python3
"""Where a sampled thread's time goes in guest terms.

Takes a psample thread file (street-bench.sh PROFILE=dir) of a build made with
LINES=1 ./build.sh (line tables) and resolves each sampled host address to its
generated line, the guest label above it (L_<pc>:) and the host function
around it: a leaf or call function (recomp_leaf_/recomp_fn_), or a unit body
(recomp_unit_NNNN_entry: code the generator left in unit form).

  tools/guest-profile.py <thread file> [top n, default 30]
      BUILD_DIR (default build): the unstripped build; OUT (default out, or
      <BUILD_DIR>.out): the packaged binary the console ran (its load address
      gives the offset psample printed); GENERATED (default
      upstream/profiles/vcs/generated): the units that build was made from.
Prints the share of the samples by kind, the top host functions, and for the
unit bodies the top guest labels (to look up in the generator's selection log,
PSPRECOMP_SELECTION_LOG=1, why that function stayed in its unit).
"""
import collections
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
build = os.environ.get('BUILD_DIR', 'build')
out = os.environ.get('OUT', 'out' if build == 'build' else build + '.out')
binary = f'{build}/bin/Release/VCSNative'
packaged = f'{out}/gtavcs-psp/VCSNative'


def first_load(path):
    elf = open(os.path.join(HERE, path), 'rb').read(4096)
    phoff = struct.unpack_from('<I', elf, 0x1C)[0]
    phentsize, phnum = struct.unpack_from('<HH', elf, 0x2A)
    loads = [struct.unpack_from('<8I', elf, phoff + i * phentsize) for i in range(phnum)]
    return min(p[2] for p in loads if p[0] == 1)


def main():
    top = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    base = first_load(packaged)
    samples = []
    total_listed = 0.0
    for line in open(sys.argv[1]):
        match = re.match(r'\s*([0-9.]+)% VCSNative[.\w]*\+0x([0-9a-f]+)\s*$', line)
        if match:
            samples.append((float(match.group(1)), int(match.group(2), 16) + base))
            total_listed += float(match.group(1))
    addresses = ' '.join('0x%x' % address for _, address in samples)
    result = subprocess.run(
        ['docker', 'run', '--rm', '-v', f'{HERE}:/w', '-w', '/w', 'vcs-recomp-builder', 'sh', '-c',
         f'arm-linux-gnueabihf-addr2line -f -e {binary} {addresses}'],
        capture_output=True, text=True, check=True).stdout.split('\n')
    labels = {}       # file -> sorted [(line, label)]

    def label_at(path, number):
        if path not in labels:
            found = []
            local = os.path.join(HERE, os.environ.get('GENERATED', 'upstream/profiles/vcs/generated'), os.path.basename(path))
            for index, text in enumerate(open(local), 1):
                match = re.match(r'(L_[0-9A-F]{8}):', text)
                if match:
                    found.append((index, match.group(1)))
            labels[path] = found
        best = '?'
        for index, name in labels[path]:
            if index > number:
                break
            best = name
        return best

    kinds = collections.Counter()
    functions = collections.Counter()
    unit_labels = collections.Counter()
    for (share, _), function, where in zip(samples, result[0::2], result[1::2]):
        match = re.search(r'recomp_(fn|leaf|unit)_([0-9A-Fa-f]+)', function)
        kind = {'fn': 'call functions', 'leaf': 'leaf functions', 'unit': 'unit bodies'}[match.group(1)] if match else 'host code'
        kinds[kind] += share
        name = match.group(0) if match else re.sub(r'^_ZN\d*', '', function)[:60]
        functions[name] += share
        if match and match.group(1) == 'unit' and 'generated_unit_' in where:
            path, _, number = where.rpartition(':')
            number = int(re.match(r'\d+', number).group(0)) if re.match(r'\d+', number) else 0
            unit_labels[f'{label_at(path, number)} ({os.path.basename(path)})'] += share
    print('listed samples: %.1f%% of the thread' % total_listed)
    for kind, share in kinds.most_common():
        print('  %5.1f%%  %s' % (share, kind))
    print('top host functions:')
    for name, share in functions.most_common(top):
        print('  %5.1f%%  %s' % (share, name))
    print('top guest labels in unit bodies:')
    for name, share in unit_labels.most_common(top):
        print('  %5.1f%%  %s' % (share, name))


if __name__ == '__main__':
    main()
