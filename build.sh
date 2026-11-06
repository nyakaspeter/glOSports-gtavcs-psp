#!/bin/sh
# Cross-build VCSNative for goodluckOS (armhf, Cortex-A7) in Docker.
#   ./build.sh              configure (first time) and build into build/
#   ./build.sh <target>...  build only the named ninja targets
#   PGO=use ./build.sh      profile-guided build with the profile in pgo/
#   PGO=generate ./build.sh instrumented build; tools/pgo.sh train runs it on
#                           the console, it writes its profile to /dev/shm/vcspgo
# The default is PGO=use when pgo/ has a profile, otherwise none. Changing PGO
# or GEN_OPT reconfigures and rebuilds everything.
# GEN_OPT=<n> optimisation level of the generated units (default 3; upstream
# builds them at -O2; LCS measured -O3 0.5-1 fps faster).
# JOBS=<n> parallel compiles (default 8; the big generated units need about
# 1 GB each, instrumented -O3 ones ~1.5 GB: JOBS=6 for those). BUILD_DIR=<dir>
# (default build) builds in another directory, its profile in <dir>.pgo.
# upstream/ is OverkillLabs3/vice-city-stories-recomp at $COMMIT with
# patches/ applied.
set -eu
cd "$(dirname "$0")"
COMMIT=8d15d83
if [ ! -d upstream ]; then
    git clone https://github.com/OverkillLabs3/vice-city-stories-recomp upstream
    git -C upstream checkout -q "$COMMIT"
    # Generated patches over 40 MB are stored xz-compressed (GitHub file size limit).
    for p in patches/[0-9]*; do [ -e "$p" ] || continue; case $p in *.xz) xz -dc "$p" | git -C upstream apply;; *) git -C upstream apply "../$p";; esac; done
fi
B=${BUILD_DIR:-build}
if [ "$B" = build ]; then PGO_DIR=${PGO_DIR:-pgo}; else PGO_DIR=${PGO_DIR:-$B.pgo}; fi
if [ -z "${PGO:-}" ]; then
    if ls "$PGO_DIR"/*.gcda >/dev/null 2>&1; then PGO=use; else PGO=off; fi
fi
case "$PGO" in
    generate) flags="-fprofile-generate=/dev/shm/vcspgo -DVCS_PGO_GENERATE" ;;
    # Code that changed since the profile was taken just goes unprofiled.
    # -fprofile-correction: the game's threads update shared counters without
    # locking, so some counts come out slightly inconsistent.
    use) flags="-fprofile-use=/w/$PGO_DIR -fprofile-correction -fprofile-partial-training -Wno-missing-profile -Wno-coverage-mismatch" ;;
    off) flags="" ;;
    *) echo "PGO must be generate, use or off"; exit 2 ;;
esac
gen_opt=${GEN_OPT:-3}
targets=${*:-VCSNative}
echo "PGO=$PGO GEN_OPT=$gen_opt BUILD_DIR=$B PGO_DIR=$PGO_DIR"
docker buildx build --load -t vcs-recomp-builder . >/dev/null
# One build per directory at a time: a build left running (e.g. after Ctrl-C) is stopped.
name="vcs-recomp-build-$(basename "$PWD")-$B"
docker rm -f "$name" >/dev/null 2>&1 || true
docker run --rm --name "$name" -v "$PWD":/w -w /w vcs-recomp-builder sh -c "
    # Setting CMAKE_CXX_FLAGS replaces the toolchain file's *_FLAGS_INIT, so the
    # A33 flags (Cortex-A7, NEON, VFPv4) are passed here too. No fused
    # multiply-add contraction: float results stay as the PSP's. Not
    # position-independent: PIE reserves a register for the GOT base in every
    # generated function.
    A33='-mcpu=cortex-a7 -mtune=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -ffp-contract=off -fno-pie'
    [ -f $B/build.ninja ] && [ \"\$(cat $B/.config 2>/dev/null)\" = '$PGO-O$gen_opt' ] ||
        cmake -S upstream -B $B -G Ninja \
            -DCMAKE_TOOLCHAIN_FILE=/w/toolchain-armhf.cmake \
            -DCMAKE_BUILD_TYPE=Release -DPSPRECOMP_PROFILE=vcs \
            -DPSPRECOMP_VCS_GE_BACKEND=GLES2 \
            -DPSPRECOMP_BUILD_TESTS=OFF -DPSPRECOMP_BUILD_PROFILE_TESTS=OFF \
            -DPSPRECOMP_AOT_ASSUME_NO_WRITE_WATCH=ON -DPSPRECOMP_AOT_PRODUCTION_FASTPATHS=ON \
            -DPSPRECOMP_GENERATED_OPT_LEVEL=$gen_opt \
            -DCMAKE_C_FLAGS=\"\$A33 $flags\" -DCMAKE_CXX_FLAGS=\"\$A33 $flags\" -DCMAKE_EXE_LINKER_FLAGS='-no-pie $flags'
    echo '$PGO-O$gen_opt' > $B/.config
    ninja -C $B -j${JOBS:-8} $targets"
[ "$targets" = VCSNative ] && file "$B"/bin/Release/VCSNative 2>/dev/null || true
