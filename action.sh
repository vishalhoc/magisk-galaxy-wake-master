#!/system/bin/sh
# Launch Galaxy Wake Master Web UI via Magisk Action Button
# Author: hoc

MODDIR=${0%/*}
BUSYBOX="/data/adb/magisk/busybox"
[ ! -x "$BUSYBOX" ] && BUSYBOX=$(which busybox 2>/dev/null)

# Ensure httpd is running on port 8096
if ! pgrep -f "httpd.*8096" >/dev/null 2>&1; then
    if [ -x "$BUSYBOX" ]; then
        "$BUSYBOX" httpd -p 0.0.0.0:8096 -h "$MODDIR/web" -c "$MODDIR/web/httpd.conf" 2>/dev/null
    fi
fi

# Ensure wake_master daemon is running
if ! pgrep -f "wake_master run" >/dev/null 2>&1; then
    nohup "$MODDIR/system/bin/wake_master" run >/dev/null 2>&1 &
fi

# Open Web UI in default Android browser
am start -a android.intent.action.VIEW -d "http://127.0.0.1:8096" 2>/dev/null

exit 0
