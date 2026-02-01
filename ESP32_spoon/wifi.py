# wifi.py
import network # pyright: ignore[reportMissingImports]
import utime # pyright: ignore[reportMissingImports]
import config

def connect_blocking():
    wlan = network.WLAN(network.STA_IF)

    wlan.active(False)
    utime.sleep_ms(200)
    wlan.active(True)
    utime.sleep_ms(200)

    try:
        wlan.config(pm=0xa11140)  # disable power-save
    except:
        pass

    attempt = 0
    while not wlan.isconnected():
        attempt += 1
        try:
            wlan.disconnect()
        except:
            pass

        print("WiFi connect attempt", attempt)
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        t0 = utime.ticks_ms()
        while (not wlan.isconnected()) and utime.ticks_diff(utime.ticks_ms(), t0) < 20000:
            utime.sleep_ms(250)

        if not wlan.isconnected():
            st = None
            try:
                st = wlan.status()
            except:
                pass
            print("WiFi not connected, status:", st, "- retry")
            utime.sleep_ms(800)

    print("ESP32 IP:", wlan.ifconfig()[0])
    return wlan

def ensure_connected(wlan):
    if wlan.isconnected():
        return wlan
    print("WiFi dropped -> reconnect")
    return connect_blocking()
