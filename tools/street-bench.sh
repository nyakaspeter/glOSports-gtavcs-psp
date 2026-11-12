#!/bin/sh
# VCS benchmark on a busy street, without touching the console: launch, skip
# the credits with two presses of A (the game then loads the save in
# game/PSP/SAVEDATA), wait for gameplay (over 100 PSP draws a frame), write the
# TELEPORT position into the player ped's matrix (this EBOOT: position at
# guest 0x098B0930; twice, the first write leaves an interior), wait STREAM
# seconds (default 12) for the area to load, then measure SECS seconds
# (default 12) of the FPS log: mean, minimum, lines under 29, PSP and GL
# draws a frame, each thread's CPU share.
#   tools/street-bench.sh [binary in ports/gtavcs-psp] [VAR=value ...]
#   TELEPORT="x y z"  default "-800 -500 12.5": the avenue through Little
#     Havana (the game's time of day is the save's plus the run's own time).
#   SWEEP="dx dy hops interval"  moves the player by (dx, dy) metres `hops`
#     times, every `interval` seconds, during the measurement (streaming,
#     traffic and peds as when driving; no vehicle physics). Along the avenue:
#     SWEEP="-3 40 6 2".
#   PROFILE=dir samples the 3 busiest threads afterwards (psample, 10 s each)
#     into dir/thread-<tid>.txt.  SHOT=file.png saves a screenshot.
#   DURING=dir samples the busiest thread so far (the game thread) while the
#     measurement runs, moves included, into dir/game.txt
#     (tools/guest-profile.py names it in guest terms).
#   FRAMELOG=file saves the measured frames' [frame-time] lines (the game
#     thread's time per vblank wait: frame, GE wait, present, I/O, guest CPU).
#   IOCTL=1 preloads glos/testing/ioctlcount.so (the driver's kernel calls by
#     kind, calls and ms per second, every 2 s in /dev/shm/vcs.log) and prints
#     the last report.
#   KEEP=1 leaves the game running.
# Needs glos/testing on the console (../goodluckOS-tools/testing-sync.sh gtavcs-psp).
set -eu
cd "$(dirname "$0")/../../goodluckOS-tools"
./console-idle.sh >/dev/null || { echo "console busy"; exit 1; }
binary=${1:-VCSNative}
[ $# -gt 0 ] && shift
P=/home/player/ports/gtavcs-psp
T=$P/glos/testing
pos() { python3 -c 'import struct, sys
print("".join("\\%03o" % b for b in struct.pack("<3f", *map(float, sys.argv[1:4]))))' "$@"; }
set_tp=${TELEPORT:--800 -500 12.5}
tp=$(pos $set_tp)
hops=''
interval=2
if [ -n "${SWEEP:-}" ]; then
    hops=$(python3 -c 'import struct, sys
x, y, z = map(float, sys.argv[1].split()[:3]); s = sys.argv[2].split()
for k in range(1, int(s[2]) + 1):
    print("\x27" + "".join("\\%03o" % b for b in struct.pack("<3f", x + float(s[0]) * k, y + float(s[1]) * k, z)) + "\x27")' "$set_tp" "$SWEEP" | tr '\n' ' ')
    interval=$(echo "$SWEEP" | awk '{print $4}')
fi
secs=${SECS:-12}
preload=''
[ -n "${IOCTL:-}" ] && preload='; s|glos/fbpan.so}|glos/fbpan.so:\$PWD/glos/testing/ioctlcount.so}|'
[ -n "${FRAMELOG:-}" ] && set -- "$@" PSPRECOMP_FRAME_TIME_DIAG=1
out=$(mktemp)
GLOS_TIMEOUT=900 python3 -I console.py "/usr/local/bin/appctl stop-application; w=0; while pidof VCSNative $binary >/dev/null && [ \$w -lt 30 ]; do sleep 1; w=\$((w+1)); done; sleep 4
cd $P
sed 's|\./VCSNative |./$binary |; s|^cd .*dirname.*|cd $P|$preload' start.sh > glos/testing/start.bench.sh; chmod +x glos/testing/start.bench.sh
a=0; while [ \$a -lt 3 ]; do /usr/local/bin/appctl launch-application \"cd $P && env VCS_FPS_LOG=1 $* ./glos/testing/start.bench.sh\"; sleep 20; ps w | grep -q '[.]/$binary' && break; a=\$((a+1)); done
$T/padpress a 600; sleep 4; $T/padpress a 600
i=0; while [ \$i -lt 60 ]; do grep 'glos: FPS' /dev/shm/vcs.log | tail -1 | awk 'BEGIN {r=1} {r=!(\$5 > 100)} END {exit r}' && break; sleep 2; i=\$((i+1)); done
sleep 6; p=\$(pidof $binary); m=\$(grep -m1 psprecomp-vram /proc/\$p/maps | cut -d- -f1); seek=\$((0x\$m - 0x04000000 + 0x098B0930))
printf '$tp' | dd of=/proc/\$p/mem bs=1 seek=\$seek conv=notrunc 2>/dev/null; sleep 6
printf '$tp' | dd of=/proc/\$p/mem bs=1 seek=\$seek conv=notrunc 2>/dev/null; sleep ${STREAM:-12}
for t in /proc/\$p/task/*; do echo \"\$(basename \$t) \$(cut -d' ' -f14,15 \$t/stat)\"; done > /dev/shm/bench.a
n0=\$(wc -l < /dev/shm/vcs.log)
if [ -n \"$hops\" ]; then (for h in $hops; do sleep $interval; printf \"\$h\" | dd of=/proc/\$p/mem bs=1 seek=\$seek conv=notrunc 2>/dev/null; done) & fi
if [ -n \"${DURING:-}\" ]; then g=\$(sort -k2 -n -r /dev/shm/bench.a | head -1 | cut -d' ' -f1); $T/psample \$g $secs 250 2000 > /dev/shm/prof.game.txt; else sleep $secs; fi; wait
for t in /proc/\$p/task/*; do echo \"\$(basename \$t) \$(cut -d' ' -f14,15 \$t/stat)\"; done > /dev/shm/bench.b
echo \"player at \$(dd if=/proc/\$p/mem bs=4 skip=\$((seek / 4)) count=3 2>/dev/null | od -A n -t x4)\"
tail -n +\$((n0 + 1)) /dev/shm/vcs.log | grep 'glos: FPS' | awk 'BEGIN {m=999} {f+=\$3; d+=\$5; g+=\$7; n++; if (\$3 < m) m=\$3; if (\$3 < 29) u++} END {if (n) printf \"fps %.1f  min %.1f  under 29: %d of %d  psp draws/frame %.0f  gl draws/frame %.0f\\n\", f/n, m, u, n, d/n, g/n; else print \"no frames logged\"}'
tail -n +\$((n0 + 1)) /dev/shm/vcs.log | grep 'glos: render thread' | awk '{i+=\$6; u+=\$8; d+=\$12; c+=\$16; n++} END {if (n) printf \"render thread ms/frame: idle %.1f  uploads %.1f  draws %.1f  cpu %.1f\\n\", i/n, u/n, d/n, c/n}'
paste /dev/shm/bench.a /dev/shm/bench.b | awk -v s=$secs '{u=(\$5+\$6)-(\$2+\$3); if (u > 5 * s) printf \"thread %s %d%%  \", \$1, u/s} END {print \"\"}'
if [ -n \"${IOCTL:-}\" ]; then grep -A2 '^ioctl/s' /dev/shm/vcs.log | tail -3 | sed 's/^/IOCTL /'; fi
if [ -n \"${FRAMELOG:-}\" ]; then echo FRAMELOG; tail -n +\$((n0 + 1)) /dev/shm/vcs.log | grep -F '[frame-time]' | sed 's/ guest_us.*//; s/[a-z_]*=//g; s/^.frame-time. //'; echo FRAMELOG-END; fi
if [ -n \"${DURING:-}\" ]; then echo DURING; cat /dev/shm/prof.game.txt; echo DURING-END; rm -f /dev/shm/prof.game.txt; fi
if [ -n \"${PROFILE:-}\" ]; then
    set -- \$(paste /dev/shm/bench.a /dev/shm/bench.b | awk '{print (\$5+\$6)-(\$2+\$3), \$1}' | sort -rn | head -3 | awk '{print \$2}')
    for t in \$1 \$2 \$3; do $T/psample \$t 10 250 1500 > /dev/shm/prof.\$t.txt; done
    for t in \$1 \$2 \$3; do echo PROFILE \$t; cat /dev/shm/prof.\$t.txt; done; rm -f /dev/shm/prof.*.txt
fi
rm -f /dev/shm/bench.a /dev/shm/bench.b" > "$out" || true
# (the console's shell prints its prompt before each line's output)
tr -d '\r' < "$out" | sed 's/^[# ]*//; /^FRAMELOG$/,$d; /^DURING$/,$d; /^PROFILE [0-9]* *$/,$d' | grep -E '^(fps|thread|render|player|no frames|IOCTL)' || tail -5 "$out"
if [ -n "${FRAMELOG:-}" ]; then
    # columns: vblank frame_us ge_us ge_async_wait_us present_us io_us cpu_us guest_cpu_us
    tr -d '\r' < "$out" | sed 's/^[# ]*//' | sed -n '/^FRAMELOG$/,/^FRAMELOG-END$/p' | grep '^[0-9]' > "$FRAMELOG"
fi
if [ -n "${DURING:-}" ]; then
    mkdir -p "$DURING"
    tr -d '\r' < "$out" | sed 's/^[# ]*//' | sed -n '/^DURING$/,/^DURING-END$/p' | sed '1d;$d' > "$DURING/game.txt"
fi
if [ -n "${PROFILE:-}" ]; then
    mkdir -p "$PROFILE"
    tr -d '\r' < "$out" | sed 's/^[# ]*//' | awk -v dir="$PROFILE" '/^PROFILE [0-9]+ *$/ {f = dir "/thread-" $NF ".txt"; next} f {print > f}'
fi
rm -f "$out"
[ -n "${SHOT:-}" ] && ./shot.sh gtavcs-psp "$SHOT" 2 >/dev/null
if [ -z "${KEEP:-}" ]; then
    # (appctl returns before the game has gone: wait, or the next run finds the console busy)
    python3 -I console.py "/usr/local/bin/appctl stop-application; w=0; while pidof $binary >/dev/null && [ \$w -lt 30 ]; do sleep 1; w=\$((w+1)); done; sleep 2; rm -f $T/start.bench.sh" >/dev/null
fi
