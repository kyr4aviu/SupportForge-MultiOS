#!/bin/sh

set -eu

cleanup() {
    for pid in ${APP_PID:-} ${NOVNC_PID:-} ${VNC_PID:-} ${WM_PID:-} ${XVFB_PID:-}; do
        [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT INT TERM

Xvfb "$DISPLAY" -screen 0 1400x900x24 -nolisten tcp -ac &
XVFB_PID=$!
sleep 1

openbox-session &
WM_PID=$!

x11vnc -display "$DISPLAY" -forever -shared -nopw -rfbport 5900 -quiet &
VNC_PID=$!

websockify --web=/usr/share/novnc 6080 localhost:5900 &
NOVNC_PID=$!

python3 -m supportforge.gui &
APP_PID=$!

echo "SupportForge Linux GUI: http://localhost:6080/vnc.html?autoconnect=1&resize=scale"
wait "$APP_PID"
