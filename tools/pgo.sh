#!/bin/sh
# Profile-guided optimisation for VCSNative (as glOSports-gtalcs-psp's pgo.sh).
#   1. PGO=generate JOBS=6 ./build.sh && ./package.sh
#   2. tools/pgo.sh train     installs the instrumented build as VCSNative.pgo
#      next to VCSNative, presses Cross through the intro movies and the
#      opening cutscene of a new game (VCS_BENCH_NEW_GAME: the save is not
#      loaded) with padpress, as the benchmark (don't touch the
#      controls), walks around the barracks for ~60 s, then SIGUSR1 makes it
#      write its profile, which is fetched into pgo/ over MTP
#   3. ./build.sh && ./package.sh   (PGO=use is the default once pgo/ has a profile)
# Re-train after big code changes; a stale profile still builds, just helps less.
# Needs padpress in ports/gtavcs-psp/glos/testing/ (../goodluckOS-tools/testing-sync.sh gtavcs-psp).
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
ROOT=$(cd "$HERE/../goodluckOS-tools" && pwd)
B=${BUILD_DIR:-build}
if [ "$B" = build ]; then OUT=${OUT_DIR:-out}; PGO_DIR=${PGO_DIR:-pgo}; else OUT=${OUT_DIR:-$B.out}; PGO_DIR=${PGO_DIR:-$B.pgo}; fi
console() { (cd "$ROOT" && GLOS_TIMEOUT=${T:-60} python3 -I console.py "$1"); }

case "${1:-}" in
train)
    tmp=$(mktemp -d)
    cp "$HERE/$OUT/gtavcs-psp/VCSNative" "$tmp/VCSNative.pgo"
    # appctl stop-application returns before the game has exited; a launch
    # sent meanwhile is killed by the late shutdown.
    console "/usr/local/bin/appctl stop-application; w=0; while pidof VCSNative VCSNative.pgo >/dev/null && [ \$w -lt 30 ]; do sleep 1; w=\$((w+1)); done; rm -f /home/player/VCSNative.pgo /home/player/vcspgo.tar"
    pkill -9 -x ptpcamerad 2>/dev/null || true  # macOS claims the console's MTP interface after the first transfer
    (cd "$ROOT" && python3 -I mtp_send.py / "$tmp/VCSNative.pgo" | tail -1)
    if ! console "ls /home/player/VCSNative.pgo" | grep -q VCSNative.pgo; then
        echo "pgo.sh: VCSNative.pgo did not reach the console (MTP busy? quit Photos / kill ptpcamerad)" >&2; rm -rf "$tmp"; exit 1
    fi
    T=900 console "cd /home/player/ports/gtavcs-psp && mv /home/player/VCSNative.pgo . && chmod +x VCSNative.pgo && rm -rf /dev/shm/vcspgo
sed 's|\./VCSNative |./VCSNative.pgo |' start.sh > start.pgo.sh; chmod +x start.pgo.sh
sleep 6; rm -f /dev/shm/vcs.log
# The first launch after the launcher has started is often killed by an appd
# restart a moment later: retry until the game runs.
a=0; while [ \$a -lt 4 ]; do /usr/local/bin/appctl launch-application 'cd /home/player/ports/gtavcs-psp && env VCS_FPS_LOG=1 VCS_BENCH_NEW_GAME=1 ./start.pgo.sh'; sleep 12; pidof VCSNative.pgo >/dev/null && break; a=\$((a+1)); sleep 8; done
P=/home/player/ports/gtavcs-psp/glos/testing/padpress; sleep 20; i=0
while [ \$i -lt 150 ]; do grep 'glos: FPS' /dev/shm/vcs.log | tail -1 | awk 'BEGIN {r=1} {r=!(\$5 > 200)} END {exit r}' && break; \$P a 600; sleep 2; i=\$((i+1)); done
echo \"3D after \$i presses\"; j=0; while [ \$j -lt 18 ]; do \$P a 600; sleep 2; j=\$((j+1)); done
k=0; while [ \$k -lt 6 ]; do \$P stick y 0 4000; \$P stick rx 255 1500; \$P stick x 255 2000; sleep 2; k=\$((k+1)); done; sleep 10
kill -USR1 \$(pidof VCSNative.pgo); sleep 25; pidof VCSNative.pgo && echo 'still running?'
ls /dev/shm/vcspgo | wc -l; du -sh /dev/shm/vcspgo
cd /dev/shm/vcspgo && tar cf /home/player/vcspgo.tar . && ls -la /home/player/vcspgo.tar; rm -rf /dev/shm/vcspgo; rm -f /home/player/ports/gtavcs-psp/VCSNative.pgo /home/player/ports/gtavcs-psp/start.pgo.sh"
    pkill -9 -x ptpcamerad 2>/dev/null || true
    (cd "$ROOT" && python3 mtp_get.py vcspgo.tar "$tmp/vcspgo.tar" | tail -1)
    if ! [ -s "$tmp/vcspgo.tar" ]; then
        echo "pgo.sh: profile tar did not arrive over MTP; $PGO_DIR/ left as it was" >&2; rm -rf "$tmp"; exit 1
    fi
    rm -rf "${HERE:?}/$PGO_DIR"; mkdir -p "$HERE/$PGO_DIR"
    tar xf "$tmp/vcspgo.tar" -C "$HERE/$PGO_DIR"
    console "rm -f /home/player/vcspgo.tar"
    rm -rf "$tmp"
    echo "$(ls "$HERE/$PGO_DIR" | grep -c gcda) profile files in $PGO_DIR/ ($(du -sh "$HERE/$PGO_DIR" | cut -f1))"
    ;;
*)
    sed -n 2,11p "$0"
    exit 2
    ;;
esac
