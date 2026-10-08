#!/system/bin/sh
# ================================================================
# Galaxy Wake Master - REST API Endpoint (CGI)
# Author: hoc
# ================================================================

echo "Content-Type: application/json; charset=utf-8"
echo "Access-Control-Allow-Origin: *"
echo "Access-Control-Allow-Methods: GET, POST, OPTIONS"
echo "Access-Control-Allow-Headers: Content-Type"
echo "Cache-Control: no-cache, no-store, must-revalidate"
echo ""

CFG_FILE="/data/adb/galaxy_wake_master.cfg"
DEFAULT_CFG="/data/adb/modules/galaxy_wake_master/default.cfg"
LOG_FILE="/data/local/tmp/galaxy_wake_master.log"
PID_FILE="/data/local/tmp/galaxy_wake_master.pid"
BIN="/data/adb/modules/galaxy_wake_master/system/bin/wake_master"
[ ! -x "$BIN" ] && BIN="/system/bin/wake_master"
[ ! -x "$BIN" ] && BIN="/data/adb/wake_master"

# Read query string and POST data
QUERY="$QUERY_STRING"
POST_DATA=""
if [ "$REQUEST_METHOD" = "POST" ] && [ -n "$CONTENT_LENGTH" ] && [ "$CONTENT_LENGTH" -gt 0 ]; then
    read -r -n "$CONTENT_LENGTH" POST_DATA 2>/dev/null
    if [ -n "$POST_DATA" ]; then
        if [ -n "$QUERY" ]; then
            QUERY="${QUERY}&${POST_DATA}"
        else
            QUERY="$POST_DATA"
        fi
    fi
fi

# URL decoder helper
urldecode() {
    echo -e "$(echo "$1" | sed 's/+/ /g;s/%\([0-9A-Fa-f]\{2\}\)/\\x\1/g')"
}

# Parameter extractor
get_param() {
    param_name="$1"
    echo "$QUERY" | tr '&' '\n' | grep "^${param_name}=" | head -n1 | cut -d '=' -f 2- | tr -d '\r\n'
}

ACTION=$(get_param "action")
[ -z "$ACTION" ] && ACTION="status"

# Load config
load_cfg() {
    if [ ! -f "$CFG_FILE" ] && [ -f "$DEFAULT_CFG" ]; then
        cp -f "$DEFAULT_CFG" "$CFG_FILE" 2>/dev/null
    fi
    if [ -f "$CFG_FILE" ]; then
        . "$CFG_FILE" 2>/dev/null
    fi
}

case "$ACTION" in
    status)
        load_cfg
        
        # Check screen state
        screen_on=false
        screen_state="ASLEEP"
        if dumpsys power 2>/dev/null | grep -q "mWakefulness=Awake" || dumpsys display 2>/dev/null | grep -q "mScreenState=ON"; then
            screen_on=true
            screen_state="AWAKE"
        fi

        # Check daemon status
        daemon_running=false
        daemon_pid=0
        if [ -f "$PID_FILE" ]; then
            pid=$(cat "$PID_FILE" 2>/dev/null | tr -d '\r\n')
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                daemon_running=true
                daemon_pid=$pid
            fi
        fi
        if ! $daemon_running; then
            pid=$(pgrep -f "wake_master run" 2>/dev/null | head -n1 | tr -d '\r\n')
            if [ -n "$pid" ]; then
                daemon_running=true
                daemon_pid=$pid
            fi
        fi

        # Sensor readings from high-precision WakeSensor DEX cache
        SENSOR_TMP="/data/local/tmp/wake_sensor.tmp"
        if [ -f "$SENSOR_TMP" ]; then
            prox_raw=$(grep -o 'PROX=[^;]*' "$SENSOR_TMP" | cut -d= -f2)
            accel_raw=$(grep -o 'ACCEL=[^;]*' "$SENSOR_TMP" | cut -d= -f2)
            orientation=$(grep -o 'ORIENT=[^;]*' "$SENSOR_TMP" | cut -d= -f2)
            dist_raw=$(grep -o 'DIST=[^;]*' "$SENSOR_TMP" | cut -d= -f2)
        fi

        [ -z "$prox_raw" ] && prox_raw=$("$BIN" sensors 2>/dev/null | grep "Proximity:" | cut -d ' ' -f 2)
        [ -z "$prox_raw" ] && prox_raw="0"
        if [ "$prox_raw" = "1" ]; then
            prox_state="NEAR"
        else
            prox_state="FAR"
        fi

        [ -z "$accel_raw" ] && accel_raw=$("$BIN" sensors 2>/dev/null | grep "Accel XYZ:" | cut -d ' ' -f 3-)
        [ -z "$accel_raw" ] && accel_raw="0.0,0.0,9.8"

        [ -z "$orientation" ] && orientation=$("$BIN" sensors 2>/dev/null | grep "Orientation:" | cut -d ' ' -f 2)
        [ -z "$orientation" ] && orientation="FACE_UP"


        # Hardware wakeup keys
        sec_keys=$(cat /sys/class/sec/sec_key/wakeup_keys 2>/dev/null | tr -d '\r\n')
        [ -z "$sec_keys" ] && sec_keys="N/A"

        # Device info
        model=$(getprop ro.product.model)
        brand=$(getprop ro.product.brand)
        android_ver=$(getprop ro.build.version.release)
        oneui_ver=$(getprop ro.build.version.oneui)

        cat <<EOF
{
  "success": true,
  "device": {
    "model": "${brand} ${model}",
    "android": "${android_ver}",
    "oneui": "${oneui_ver:-5.1}"
  },
  "daemon": {
    "running": ${daemon_running},
    "pid": ${daemon_pid}
  },
  "screen": {
    "is_on": ${screen_on},
    "state": "${screen_state}"
  },
  "sensors": {
    "proximity_raw": "${prox_raw}",
    "proximity_state": "${prox_state}",
    "accel_raw": "${accel_raw}",
    "orientation": "${orientation}"
  },
  "hardware": {
    "sec_wakeup_keys": "${sec_keys}"
  },
  "config": {
    "vol_up_wake": ${VOL_UP_WAKE:-1},
    "vol_down_wake": ${VOL_DOWN_WAKE:-1},
    "drop_vol_on_wake": ${DROP_VOL_ON_WAKE:-1},
    "headset_hook_wake": ${HEADSET_HOOK_WAKE:-0},
    "put_down_sleep": ${PUT_DOWN_SLEEP:-1},
    "face_down_sleep": ${FACE_DOWN_SLEEP:-1},
    "pocket_sleep": ${POCKET_SLEEP:-1},
    "flat_table_sleep": ${FLAT_TABLE_SLEEP:-0},
    "sleep_delay": ${SLEEP_DELAY:-2},
    "hw_sysfs_wake": ${HW_SYSFS_WAKE:-1},
    "vibrate_feedback": ${VIBRATE_FEEDBACK:-1},
    "web_port": ${WEB_PORT:-8096}
  }
}
EOF
        ;;

    save_config)
        # Parse inputs
        v_up=$(get_param "vol_up_wake")
        v_down=$(get_param "vol_down_wake")
        v_drop=$(get_param "drop_vol_on_wake")
        v_headset=$(get_param "headset_hook_wake")
        p_sleep=$(get_param "put_down_sleep")
        f_sleep=$(get_param "face_down_sleep")
        pk_sleep=$(get_param "pocket_sleep")
        ft_sleep=$(get_param "flat_table_sleep")
        s_delay=$(get_param "sleep_delay")
        h_wake=$(get_param "hw_sysfs_wake")
        v_feed=$(get_param "vibrate_feedback")

        # Sanitize defaults if empty
        [ -z "$v_up" ] && v_up=1
        [ -z "$v_down" ] && v_down=1
        [ -z "$v_drop" ] && v_drop=1
        [ -z "$v_headset" ] && v_headset=0
        [ -z "$p_sleep" ] && p_sleep=1
        [ -z "$f_sleep" ] && f_sleep=1
        [ -z "$pk_sleep" ] && pk_sleep=1
        [ -z "$ft_sleep" ] && ft_sleep=0
        [ -z "$s_delay" ] && s_delay=2
        [ -z "$h_wake" ] && h_wake=1
        [ -z "$v_feed" ] && v_feed=1

        cat <<EOF > "$CFG_FILE"
# Galaxy Wake Master Configuration (Updated via Web UI)
VOL_UP_WAKE=${v_up}
VOL_DOWN_WAKE=${v_down}
DROP_VOL_ON_WAKE=${v_drop}
HEADSET_HOOK_WAKE=${v_headset}
PUT_DOWN_SLEEP=${p_sleep}
FACE_DOWN_SLEEP=${f_sleep}
POCKET_SLEEP=${pk_sleep}
FLAT_TABLE_SLEEP=${ft_sleep}
SLEEP_DELAY=${s_delay}
HW_SYSFS_WAKE=${h_wake}
VIBRATE_FEEDBACK=${v_feed}
WEB_PORT=8096
EOF

        # Re-apply hardware pins if enabled
        if [ "$h_wake" = "1" ] && [ -x "$BIN" ]; then
            "$BIN" apply_hw >/dev/null 2>&1 &
        fi

        cat <<EOF
{
  "success": true,
  "message": "Configuration saved and applied instantly!"
}
EOF
        ;;

    sleep)
        if [ -x "$BIN" ]; then
            "$BIN" sleep >/dev/null 2>&1 &
        else
            input keyevent 223 2>/dev/null || input keyevent 26 2>/dev/null &
        fi
        cat <<EOF
{
  "success": true,
  "message": "Screen put to sleep."
}
EOF
        ;;

    wake)
        if [ -x "$BIN" ]; then
            "$BIN" wake >/dev/null 2>&1 &
        else
            input keyevent 224 2>/dev/null || input keyevent 26 2>/dev/null &
        fi
        cat <<EOF
{
  "success": true,
  "message": "Screen woke up."
}
EOF
        ;;

    power_menu)
        if [ -x "$BIN" ]; then
            "$BIN" power_menu >/dev/null 2>&1 &
        else
            input keyevent --longpress 26 2>/dev/null || am broadcast -a android.intent.action.ACTION_SHOW_POWER_DIALOG 2>/dev/null &
        fi
        cat <<EOF
{
  "success": true,
  "message": "Power dialog triggered on screen."
}
EOF
        ;;

    lock)
        input keyevent 223 2>/dev/null &
        cat <<EOF
{
  "success": true,
  "message": "Device locked."
}
EOF
        ;;

    screenshot)
        input keyevent 120 2>/dev/null &
        cat <<EOF
{
  "success": true,
  "message": "Screenshot captured."
}
EOF
        ;;

    restart_systemui)
        (
            sleep 1
            pkill -9 -f "com.android.systemui" 2>/dev/null || kill -9 $(pidof com.android.systemui) 2>/dev/null
        ) &
        cat <<EOF
{
  "success": true,
  "message": "System UI restart triggered."
}
EOF
        ;;

    restart_daemon)
        if [ -x "$BIN" ]; then
            "$BIN" restart >/dev/null 2>&1 &
        fi
        cat <<EOF
{
  "success": true,
  "message": "Galaxy Wake Master daemon restarted."
}
EOF
        ;;

    reboot)
        mode=$(getparam "mode")
        (
            sleep 1
            case "$mode" in
                recovery) reboot recovery 2>/dev/null ;;
                bootloader|download) reboot bootloader 2>/dev/null || reboot download 2>/dev/null ;;
                poweroff) reboot -p 2>/dev/null ;;
                *) reboot 2>/dev/null ;;
            esac
        ) &
        cat <<EOF
{
  "success": true,
  "message": "Reboot (${mode:-system}) initiated."
}
EOF
        ;;

    get_logs)
        log_content=""
        if [ -f "$LOG_FILE" ]; then
            log_content=$(tail -n 40 "$LOG_FILE" 2>/dev/null | tr '\n' '\t' | sed 's/"/\\"/g' | tr '\t' '\n' | sed 's/$/\\n/' | tr -d '\n')
        fi
        cat <<EOF
{
  "success": true,
  "logs": "${log_content}"
}
EOF
        ;;

    *)
        cat <<EOF
{
  "success": false,
  "error": "Unknown action: ${ACTION}"
}
EOF
        ;;
esac

exit 0
