import utime # pyright: ignore[reportMissingImports]
import configAcc
import wifi
from osc_client import OSCClient
from accelerometre import DetecteurTouillage

print("=== WIFI ===")
wlan = wifi.connect_blocking()

print("=== OSC CLIENT ===")
osc = OSCClient(configAcc.OSC_TARGET_IP, configAcc.OSC_TARGET_PORT)

print("=== ACCÉLÉRO ===")
det = DetecteurTouillage()
det.demarrer()

last_dbg = utime.ticks_ms()

while True:
    wlan = wifi.ensure_connected(wlan)

    data = det.update()

    # Print humain
    if data["event"] == 1:
        if data["event_dir"] == 1:
            print("rotation droite")
        else:
            print("rotation gauche")

    # OSC stream (1 message)
    # args: device_id(hash), active, dir, event, event_dir, lateral_g, angle_deg, energy, count
    # device_id en int: simple hash stable
    dev = 0
    for c in configAcc.DEVICE_ID:
        dev = (dev * 31 + ord(c)) & 0x7fffffff

    osc.send(
        configAcc.OSC_ADDR_STATE,
        dev,
        int(data["active"]),
        int(data["dir"]),
        int(data["event"]),
        int(data["event_dir"]),
        float(data["lateral_g"]),
        float(data["angle_deg"]),
        float(data["energy"]),
        int(data["count"]),
    )

    if data["event"] == 1:
        osc.send(
            configAcc.OSC_ADDR_EVENT,
            dev,
            int(data["event_dir"]),
            int(data["count"])
        )

    if utime.ticks_diff(utime.ticks_ms(), last_dbg) > configAcc.DEBUG_INTERVAL_MS:
        print(
            "DBG",
            "active", data["active"],
            "dir", data["dir"],
            "lat", "{:.3f}".format(data["lateral_g"]),
            "angle", "{:.1f}".format(data["angle_deg"]),
            "energy", "{:.1f}".format(data["energy"]),
            "count", data["count"],
        )
        last_dbg = utime.ticks_ms()

    utime.sleep_ms(configAcc.LOOP_PERIOD_MS)
