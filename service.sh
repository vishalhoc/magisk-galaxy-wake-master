#!/system/bin/sh
# ================================================================
# Galaxy Wake Master - Late Boot Service & Continuous Guardian
# Author: hoc
# ================================================================

MODDIR=${0%/*}
LOG="/data/local/tmp/galaxy_wake_master.log"

echo "[$(date)] Galaxy Wake Master Service starting" > "$LOG"

# Wait for Android boot completion
until [ "$(getprop sys.boot_completed)" = "1" ]; do
    sleep 2
done
sleep 3

chmod 755 "$MODDIR/system/bin/wake_master" 2>/dev/null
chmod 755 "$MODDIR/web/cgi-bin/api.cgi" 2>/dev/null
chmod 755 "$MODDIR/action.sh" 2>/dev/null

cp "$MODDIR/system/bin/wake_master" /data/adb/wake_master 2>/dev/null
chmod 755 /data/adb/wake_master 2>/dev/null

# Default configuration file
CFG_FILE="/data/adb/galaxy_wake_master.cfg"
if [ ! -f "$CFG_FILE" ] && [ -f "$MODDIR/default.cfg" ]; then
    cp -f "$MODDIR/default.cfg" "$CFG_FILE" 2>/dev/null
fi

# Apply Hardware Wakeup Pins
sh "$MODDIR/system/bin/wake_master" apply_hw >> "$LOG" 2>&1

# Find busybox
BUSYBOX="/data/adb/magisk/busybox"
[ ! -x "$BUSYBOX" ] && BUSYBOX="/system/bin/busybox"
[ ! -x "$BUSYBOX" ] && BUSYBOX=$(which busybox 2>/dev/null)

start_web_daemon() {
    if ! pgrep -f "httpd.*8096" >/dev/null 2>&1; then
        pkill -9 -f "8096" 2>/dev/null
        sleep 1
        if [ -x "$BUSYBOX" ]; then
            "$BUSYBOX" httpd -p 0.0.0.0:8096 -h "$MODDIR/web" -c "$MODDIR/web/httpd.conf"
            echo "[*] Web UI started on http://127.0.0.1:8096" >> "$LOG"
        fi
    fi
}

start_wake_daemon() {
    if ! pgrep -f "wake_master run" >/dev/null 2>&1; then
        nohup "$MODDIR/system/bin/wake_master" run >> "$LOG" 2>&1 &
        echo "[*] Wake Master daemon launched (PID: $!)" >> "$LOG"
    fi
}

# Start daemons
start_web_daemon
start_wake_daemon

# Background Persistent Guardian Loop (runs detached)
(
    while true; do
        sleep 10
        # 1. Keep Web UI alive
        start_web_daemon
        # 2. Keep Wake daemon alive
        start_wake_daemon
        # 3. Ensure hardware sysfs wakeup keys remain applied
        if [ -f /sys/class/sec/sec_key/wakeup_keys ]; then
            current=$(cat /sys/class/sec/sec_key/wakeup_keys 2>/dev/null)
            if [ "$current" != "114,115,116,172" ]; then
                echo "114,115,116,172" > /sys/class/sec/sec_key/wakeup_keys 2>/dev/null
            fi
        fi
    done
) &

echo "[$(date)] Galaxy Wake Master Service & Guardian running in background" >> "$LOG"
exit 0
