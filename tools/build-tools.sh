#!/bin/sh
# Cross-compile glos/fbpan.so (the LD_PRELOAD shim start.sh uses: asynchronous
# framebuffer pan) from tools/src/fbpan.c, armhf, in the vcs-recomp-builder Docker image
# that build.sh makes. The console-side test tools are shared: goodluckOS-tools/testing/.
set -eu
cd "$(dirname "$0")/.."
docker run --rm -v "$PWD":/w -w /w vcs-recomp-builder sh -c '
arm-linux-gnueabihf-gcc -O2 -mcpu=cortex-a7 -mtune=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -shared -fPIC -o glos/fbpan.so tools/src/fbpan.c -ldl -lpthread'
ls -l glos/fbpan.so
