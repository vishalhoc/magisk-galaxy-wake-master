#!/system/bin/sh
# ================================================================
# Galaxy Wake Master - Early Boot Initialization
# Author: hoc
# ================================================================

# 1. Enable Samsung kernel sec_key driver wakeup for Volume & Power keys
if [ -f /sys/class/sec/sec_key/wakeup_keys ]; then
    echo "114,115,116,172" > /sys/class/sec/sec_key/wakeup_keys 2>/dev/null
fi

# 2. Enable kernel wakeup IRQs on input devices & keep MTK keypad powered
if [ -f /sys/devices/platform/10010000.kp/power/control ]; then
    echo "on" > /sys/devices/platform/10010000.kp/power/control 2>/dev/null
fi
for w in /sys/class/input/input*/device/power/wakeup \
         /sys/class/input/input*/power/wakeup \
         /sys/devices/platform/*kpd*/power/wakeup \
         /sys/devices/platform/*gpio*keys*/power/wakeup; do
    if [ -f "$w" ]; then
        echo "enabled" > "$w" 2>/dev/null
    fi
done

# 3. Ensure input device nodes are accessible
chmod 0666 /dev/input/event* 2>/dev/null

exit 0
