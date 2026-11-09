#!/bin/sh
# Package build/bin/Release/VCSNative for the console into out/gtavcs-psp/
# (BUILD_DIR=<dir>: from <dir>/ into <dir>.out/gtavcs-psp/; OUT_DIR overrides):
#   VCSNative (stripped, RUNPATH $ORIGIN/lib), lib/ (every library it needs
#   that goodluckOS doesn't have, listed in console-libs.txt), start.sh,
#   config/, gtavcs-psp.puppy, icon.png, glos/. The game files go in gtavcs-psp/game/ on
#   the console.
set -eu
cd "$(dirname "$0")"
B=${BUILD_DIR:-build}
if [ "$B" = build ]; then OUT=${OUT_DIR:-out}; else OUT=${OUT_DIR:-$B.out}; fi
rm -rf "$OUT" && mkdir -p "$OUT/gtavcs-psp/lib"
docker run --rm -e B="$B" -e OUT="$OUT" -v "$PWD":/w -w /w vcs-recomp-builder sh -c '
set -eu
dirs="/usr/lib/arm-linux-gnueabihf /lib/arm-linux-gnueabihf"
always_system="libc.so.6 libm.so.6 libdl.so.2 libpthread.so.0 librt.so.1 libresolv.so.2 ld-linux-armhf.so.3"
todo="$B/bin/Release/VCSNative"; seen=""
while [ -n "$todo" ]; do
    set -- $todo; f=$1; shift; todo="$*"
    for so in $(arm-linux-gnueabihf-readelf -d "$f" | sed -n "s/.*NEEDED.*\[\(.*\)\]/\1/p"); do
        case " $seen " in *" $so "*) continue ;; esac
        seen="$seen $so"
        case " $always_system " in *" $so "*) continue ;; esac
        # goodluckOS has these, but built without parts the Debian libraries
        # need (libcrypto has no ENGINE API), so they are bundled anyway.
        case " libssl.so.3 libcrypto.so.3 " in *" $so "*) ;; *)
            grep -qx "$so" console-libs.txt && continue ;; esac
        for d in $dirs; do
            if [ -e "$d/$so" ]; then
                cp -L "$d/$so" "$OUT/gtavcs-psp/lib/"
                todo="$todo $OUT/gtavcs-psp/lib/$so"
                break
            fi
        done
        [ -e "$OUT/gtavcs-psp/lib/$so" ] || echo "MISSING: $so"
    done
done
arm-linux-gnueabihf-strip -o "$OUT/gtavcs-psp/VCSNative" "$B/bin/Release/VCSNative"
arm-linux-gnueabihf-strip "$OUT"/gtavcs-psp/lib/*.so*
patchelf --set-rpath "\$ORIGIN/lib" "$OUT/gtavcs-psp/VCSNative"
for l in "$OUT"/gtavcs-psp/lib/*; do patchelf --set-rpath "\$ORIGIN" "$l"; done
'
cp start.sh gtavcs-psp.puppy icon.png "$OUT/gtavcs-psp/"
# glos/: the driver set from goodluckOS-mali-driver (the port runs on a stock
# goodluckOS with nothing installed outside its folder). glos/testing/ is not
# shipped.
GLOS=../goodluckOS-mali-driver/glos
[ -d "$GLOS" ] || { echo "package.sh: $GLOS missing (goodluckOS-mali-driver/assemble-glos.sh); the port needs glos/ next to start.sh" >&2; exit 1; }
mkdir -p "$OUT/gtavcs-psp/glos/lib"
cp "$GLOS"/glos-gpu "$GLOS"/glos-gpu-switch "$GLOS"/mali.ko "$GLOS"/glos_fbfix.ko "$OUT/gtavcs-psp/glos/" && cp "$GLOS"/lib/* "$OUT/gtavcs-psp/glos/lib/"
# fbpan.so: asynchronous framebuffer pan (LD_PRELOAD in start.sh), from
# glOSports-gtalcs-psp (tools/src/fbpan.c).
cp glos/fbpan.so "$OUT/gtavcs-psp/glos/"
mkdir -p "$OUT/gtavcs-psp/config" && cp config/VCSNative.ini "$OUT/gtavcs-psp/config/"
# The driver's program binaries of the shader variants played so far: loaded
# (and warmed) before the first frame, so a fresh install starts without the
# compiler's 10-50 ms stalls (config/shader-cache/<key>.bin, VCS_GLES_SHADER_WARMUP
# / VCS_GLES_SHADER_CACHE).
if ls config/shader-cache/*.bin >/dev/null 2>&1; then
    mkdir -p "$OUT/gtavcs-psp/config/shader-cache" && cp config/shader-cache/*.bin "$OUT/gtavcs-psp/config/shader-cache/"
fi
ls "$OUT/gtavcs-psp/lib" | wc -l; du -sh "$OUT/gtavcs-psp" "$OUT/gtavcs-psp/lib" "$OUT/gtavcs-psp/VCSNative"
