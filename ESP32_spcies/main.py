import time
import machine  # pyright: ignore[reportMissingImports]
import wifi # pyright: ignore[reportMissingImports]
import rfid_access

WIFI_SSID = "" # Name
WIFI_PASS = "" # Password

while True:
    try:
        ip = wifi.connect(WIFI_SSID, WIFI_PASS, force_reset=True)
        rfid_access.run(local_ip=ip)
    except Exception as e:
        print("CRASH:", e)
        time.sleep_ms(500)
        machine.reset()


