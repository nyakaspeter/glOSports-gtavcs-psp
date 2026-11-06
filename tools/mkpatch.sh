#!/bin/sh
# mkpatch.sh <NNNN-name> <file under upstream>...: the named files' changes
# between upstream at $COMMIT + patches/0001..(NNNN-1) and the current
# upstream/ -> patches/NNNN-name.patch. New files are included. Made with git
# diff, which keeps the CRLF line endings of the files upstream pins to CRLF.
set -eu
P=$(cd "$(dirname "$0")/.." && pwd)
COMMIT=$(sed -n 's/^COMMIT=//p' "$P/build.sh")
name=$1; shift; n=${name%%-*}
tmp=$(mktemp -d)
trap 'git -C "$P/upstream" worktree remove --force "$tmp/wt" 2>/dev/null; rm -rf "$tmp"' EXIT
git -C "$P/upstream" worktree add -q --detach "$tmp/wt" "$COMMIT"
for p in "$P"/patches/[0-9]*; do
    [ -e "$p" ] || continue
    b=$(basename "$p"); [ "${b%%-*}" -lt "$n" ] || continue
    case $p in *.xz) xz -dc "$p" | git -C "$tmp/wt" apply;; *) git -C "$tmp/wt" apply "$p";; esac
done
git -C "$tmp/wt" add -A && git -C "$tmp/wt" -c user.name=mkpatch -c user.email=mkpatch@localhost commit -qm base --allow-empty
for f in "$@"; do mkdir -p "$tmp/wt/$(dirname "$f")" && cp "$P/upstream/$f" "$tmp/wt/$f"; done
git -C "$tmp/wt" add -N -- "$@"
git -C "$tmp/wt" diff -- "$@" > "$P/patches/$name.patch"
wc -l "$P/patches/$name.patch"
