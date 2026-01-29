import network # pyright: ignore[reportMissingImports]
import time

def connect(ssid, password, max_tries=12, try_timeout_ms=3000, force_reset=True):
    wlan = network.WLAN(network.STA_IF)

    if force_reset:
        try:
            wlan.active(False)
        except Exception:
            pass
        time.sleep_ms(150)

    wlan.active(True)
    time.sleep_ms(150)

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("=== WIFI ===")
        print("Deja connecte. ESP32 IP:", ip)
        return ip

    print("=== WIFI ===")
    for attempt in range(1, max_tries + 1):
        print("WiFi connect attempt", attempt)

        try:
            wlan.disconnect()
        except Exception:
            pass

        wlan.connect(ssid, password)

        t0 = time.ticks_ms()
        while (not wlan.isconnected()) and (time.ticks_diff(time.ticks_ms(), t0) < try_timeout_ms):
            time.sleep_ms(200)

        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print("Connecte. ESP32 IP:", ip)
            return ip

        try:
            wlan.active(False)
        except Exception:
            pass
        time.sleep_ms(150)
        wlan.active(True)
        time.sleep_ms(150)

    raise RuntimeError("wifi_failed")


