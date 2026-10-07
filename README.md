# Galaxy Wake Master (Volume Wake & Put-Down Sleep)
**Author:** hoc  
**Module ID:** `galaxy_wake_master`  
**Version:** `v1.0`  
**Target:** Samsung Galaxy (One UI / Dimensity / MTK / Universal Android 10-14)  
**Control Panel:** `http://127.0.0.1:8096`

---

<p align="center">
  <img src="assets/wake_master_live_screen.png" width="48%" alt="Emergency Controls & Volume Wake" />
  <img src="assets/wake_master_scroll.png" width="48%" alt="Put-Down to Sleep & Sensors" />
</p>

---

## 🌟 Overview & Purpose
Designed specifically for smartphones where the physical **Power Button is faulty, worn out, or broken**, **Galaxy Wake Master** provides a complete, battery-friendly, zero-latency replacement system:

1. **Volume Key Wakeup**: Wake your device by pressing **Volume Up**, **Volume Down**, or **Both**.
2. **Drop Volume Event on Wake**: Prevents annoying media/ringer volume changes when waking up the display.
3. **"Put Down to Sleep" (Wake-Down)**: The natural companion to Samsung's built-in *"Lift to Wake"*. Automatically turns off the screen and locks the device when you place it face-down on a surface, put it in your pocket, or lay it flat on a table.
4. **Emergency Virtual Power Panel**: Direct on-screen controls to Sleep, Wake, open the Android Power Off / Restart dialog, take screenshots, or restart System UI.
5. **Integrated Web UI & Magisk Action Button**: Tap the **Action** button in the Magisk app (or open `http://127.0.0.1:8096`) to access the responsive dark glassmorphic control center.

---

## ⚡ How It Works Under The Hood

### 1. Dual-Layer Hardware Wakeup (Zero Sleep Delay)
- **Kernel Sysfs Layer**: Interacts with Samsung's kernel driver at `/sys/class/sec/sec_key/wakeup_keys`, setting `114,115,116,172`, and keeps MediaTek keypad controller (`10010000.kp`) power active (`echo on > /sys/devices/platform/10010000.kp/power/control`). This instructs the kernel to wake the Application Processor (AP) from deep sleep whenever Volume Up or Volume Down is pressed.
- **Systemless Keylayout Overlay**: Injects `WAKE_DROPPED` flags into `/system/usr/keylayout/Generic.kl`, `mtk-kpd.kl`, `gpio-keys.kl`, and `sec_keys.kl`.
- **Event Guardian (`wake_master`)**: A lightweight background daemon blocks on kernel input events (`getevent -l`). When a volume key is pressed while the screen is asleep, it immediately triggers `input keyevent 224` (KEYCODE_WAKEUP) and restores volume levels.

### 2. "Put Down to Sleep" (Wake-Down Engine)
- **Face-Down Detection**: Checks proximity sensor (`NEAR`) and accelerometer Z-axis ($Z < -5.0 \text{ m/s}^2$ / negative vector).
- **Pocket Auto-Sleep**: Detects vertical orientation ($Y < -5.0$) while proximity is covered (`NEAR`).
- **Configurable Trigger Delay**: Prevents false triggers while holding or moving the device (default: 2.0 seconds).
- **🛡️ ZERO Battery Drain Guarantee**: Sensor polling **ONLY runs while the screen is ON**. As soon as the display turns off, sensor monitoring immediately shuts down. The phone enters deep sleep with 0 wakeups.

---

## 📱 How To Install & Use

1. Download [`galaxy_wake_master_v1.0.zip`](https://github.com/vishalhoc/magisk-galaxy-wake-master/releases) from Releases.
2. Open the **Magisk App** -> go to **Modules** -> tap **Install from storage** -> select `galaxy_wake_master_v1.0.zip`.
3. Reboot your device.
4. After reboot, tap the **Action** button in the Magisk app (or open `http://127.0.0.1:8096`) to customize your wake keys and put-down sleep preferences!
