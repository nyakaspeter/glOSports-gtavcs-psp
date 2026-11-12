#!/bin/sh
# Repeatable VCS benchmark: the opening cutscene (Vic at Fort Baxter, ~900 GE
# draws a frame), started with VCS_BENCH_NEW_GAME=1 so a save present does not
# skip it. Skips the credits with two early presses of A (a later one would skip
# the cutscene), waits for its first 3D frames (over 200 draws), then averages
# 10 s of the FPS log 8 s later and prints per-thread CPU.
#   tools/cutscene-bench.sh <binary in ports/gtavcs-psp> [VAR=value ...]
# Needs glos/testing on the console (../goodluckOS-tools/testing-sync.sh gtavcs-psp).
set -eu
cd "$(dirname "$0")/../../goodluckOS-tools"
binary=$1
shift
GLOS_TIMEOUT=900 python3 -I console.py "/usr/local/bin/appctl stop-application; w=0; while pidof VCSNative $binary >/dev/null && [ \$w -lt 30 ]; do sleep 1; w=\$((w+1)); done; sleep 4
cd /home/player/ports/gtavcs-psp
sed 's|\./VCSNative |./$binary |; s|^cd .*dirname.*|cd /home/player/ports/gtavcs-psp|' start.sh > glos/testing/start.bench.sh; chmod +x glos/testing/start.bench.sh
T=/home/player/ports/gtavcs-psp/glos/testing
a=0; while [ \$a -lt 3 ]; do /usr/local/bin/appctl launch-application \"cd /home/player/ports/gtavcs-psp && env VCS_FPS_LOG=1 VCS_BENCH_NEW_GAME=1 $* ./glos/testing/start.bench.sh\"; sleep 20; ps w | grep -q '[.]/$binary' && break; a=\$((a+1)); done
\$T/padpress a 600; sleep 4; \$T/padpress a 600
i=0; while [ \$i -lt 120 ]; do grep 'glos: FPS' /dev/shm/vcs.log | tail -1 | awk 'BEGIN {r=1} {r=!(\$5 > 200)} END {exit r}' && break; sleep 2; i=\$((i+1)); done
sleep 8; p=\$(pidof $binary)
for t in /proc/\$p/task/*; do echo \"\$(basename \$t) \$(cut -d' ' -f14,15 \$t/stat)\"; done > /dev/shm/bench.a
n0=\$(wc -l < /dev/shm/vcs.log); sleep 10
for t in /proc/\$p/task/*; do echo \"\$(basename \$t) \$(cut -d' ' -f14,15 \$t/stat)\"; done > /dev/shm/bench.b
tail -n +\$((n0 + 1)) /dev/shm/vcs.log | grep 'glos: FPS' | awk '{f+=\$3; d+=\$5; g+=\$7; n++} END {if (n) printf \"fps %.1f  psp draws/frame %.0f  gl draws/frame %.0f  (%d samples)\\n\", f/n, d/n, g/n, n; else print \"no frames logged\"}'
paste /dev/shm/bench.a /dev/shm/bench.b | awk '{u=(\$5+\$6)-(\$2+\$3); if (u > 50) printf \"thread %s %d%%  \", \$1, u/10} END {print \"\"}'
/usr/local/bin/appctl stop-application; rm -f glos/testing/start.bench.sh /dev/shm/bench.a /dev/shm/bench.b" | tail -3
