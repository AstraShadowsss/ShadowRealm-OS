#!/bin/sh
set -eu
Xvfb :93 -screen 0 1200x800x24 >/tmp/shadowrealm-os-terminal-xvfb.log 2>&1 &
xpid=$!
trap 'kill "$xpid" 2>/dev/null || true' EXIT
export DISPLAY=:93
sleep 1
/tmp/shadowrealm-os-release-terminal -T 'ShadowRealm-OS release command test' -e /bin/bash -c 'printf "%s\n" "$1" > /tmp/shadowrealm-os-terminal-argv-result; sleep 2' bash 'argument with spaces'
pid=$!
test "$(cat /tmp/shadowrealm-os-terminal-argv-result)" = 'argument with spaces'
echo 'PASS terminal command execution and argument preservation'