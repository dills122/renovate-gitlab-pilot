#!/bin/sh
# Run on the Linux writer runner host; bind-mount this directory into writer jobs only.
set -eu
dir=${1:?Usage: setup-state.sh /absolute/path/to/runner-state}
case "$dir" in /*) ;; *) exit 2;; esac
test "$dir" != /
if [ -d "$dir" ] && [ ! -f "$dir/.pilot-state-volume" ] && [ -n "$(ls -A "$dir")" ]; then
  echo "Unrecognized nonempty state directory" >&2; exit 1
fi
install -d -m 0700 -o 12021 -g 0 "$dir"
if [ ! -f "$dir/.pilot-state-volume" ]; then
  install -m 0600 -o 12021 -g 0 /dev/null "$dir/.pilot-state-volume"
fi
