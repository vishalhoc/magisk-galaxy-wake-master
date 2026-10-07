#!/system/bin/sh
# ================================================================
# Galaxy Wake Master - Magisk Installer
# Author: hoc
# ================================================================

ui_print "********************************************"
ui_print "  Galaxy Wake Master & Power Button Bypass  "
ui_print "                  by hoc                    "
ui_print "********************************************"
ui_print " "
ui_print "Device: Samsung Galaxy (One UI / Dimensity / MTK / Universal)"
ui_print " "
ui_print "[*] Installing Hardware Wakeup Key Overlays..."
ui_print "[*] Installing Samsung sec_key Driver Enabler..."
ui_print "[*] Installing Volume-Wake Event Interceptor..."
ui_print "[*] Installing 'Put Down to Sleep' Guardian Engine..."
ui_print "[*] Installing Emergency Virtual Power Controls..."
ui_print "[*] Installing Web UI Control Panel (Port 8096)..."
ui_print " "

# Patch Generic.kl systemlessly from live device if available
if [ -f /system/usr/keylayout/Generic.kl ]; then
    ui_print "[*] Patching system Generic.kl keylayout..."
    mkdir -p "$MODPATH/system/usr/keylayout"
    cp -af /system/usr/keylayout/Generic.kl "$MODPATH/system/usr/keylayout/Generic.kl"
    sed -i -E 's/key 114([ \t]+)VOLUME_DOWN.*/key 114\1VOLUME_DOWN       WAKE_DROPPED/g' "$MODPATH/system/usr/keylayout/Generic.kl"
    sed -i -E 's/key 115([ \t]+)VOLUME_UP.*/key 115\1VOLUME_UP         WAKE_DROPPED/g' "$MODPATH/system/usr/keylayout/Generic.kl"
fi

# Patch vendor keylayouts if present on device
for kl in /vendor/usr/keylayout/mtk-kpd.kl /vendor/usr/keylayout/gpio-keys.kl /vendor/usr/keylayout/sec_keys.kl; do
    if [ -f "$kl" ]; then
        fname=$(basename "$kl")
        mkdir -p "$MODPATH/system/vendor/usr/keylayout"
        cp -af "$kl" "$MODPATH/system/vendor/usr/keylayout/$fname"
        sed -i -E 's/key 114([ \t]+)VOLUME_DOWN.*/key 114\1VOLUME_DOWN       WAKE_DROPPED/g' "$MODPATH/system/vendor/usr/keylayout/$fname"
        sed -i -E 's/key 115([ \t]+)VOLUME_UP.*/key 115\1VOLUME_UP         WAKE_DROPPED/g' "$MODPATH/system/vendor/usr/keylayout/$fname"
    fi
done

# Initialize default configuration if not already configured
CFG_FILE="/data/adb/galaxy_wake_master.cfg"
if [ ! -f "$CFG_FILE" ] && [ -f "$MODPATH/default.cfg" ]; then
    ui_print "[*] Creating default configuration at $CFG_FILE..."
    cp -f "$MODPATH/default.cfg" "$CFG_FILE"
fi

# Set permissions
set_perm_recursive $MODPATH 0 0 0755 0644
set_perm_recursive $MODPATH/system/bin 0 0 0755 0755
set_perm $MODPATH/service.sh 0 0 0755
set_perm $MODPATH/post-fs-data.sh 0 0 0755
set_perm $MODPATH/action.sh 0 0 0755
set_perm $MODPATH/web/cgi-bin/api.cgi 0 0 0755

# Symlink to /data/adb/wake_master for quick terminal access
cp -f "$MODPATH/system/bin/wake_master" /data/adb/wake_master 2>/dev/null
chmod 0755 /data/adb/wake_master 2>/dev/null

ui_print " "
ui_print "=========================================="
ui_print "✅ Installation successful!"
ui_print "   Web Control Panel: http://127.0.0.1:8096"
ui_print "   Tap 'Action' button in Magisk app or run"
ui_print "   'su -c wake_master' in any terminal."
ui_print "   Please REBOOT your device to activate."
ui_print "=========================================="
