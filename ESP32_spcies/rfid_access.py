from machine import Pin, SPI # pyright: ignore[reportMissingImports]
import time
from mfrc522 import MFRC522 # pyright: ignore[reportMissingImports]
from osc_client import OSCClient  # pyright: ignore[reportMissingImports]

# ====== CONFIG ======
SPICE_ID      = X  # pyright: ignore[reportUndefinedVariable]
SPICE_UID_HEX = "xxxxxxxx"   # remplace par l'UID réel
SPICE_NAME    = "epice x"

PIN_SCK  = 18
PIN_MOSI = 27
PIN_MISO = 19
PIN_CS   = 21
PIN_RST  = 22
SPI_ID   = 2

DIRECTOR_IP   = "00.00.000.000" # Mettre la bonne ip
DIRECTOR_PORT = 8000.           # Mettre le bon port
# ===============================

START_STABLE_MS       = 3000
ABSENCE_MS_TO_TRIGGER = 3000
PRESENT_GRACE_MS      = 250
LOG_EVERY_MS          = 500

HEARTBEAT_EVERY_MS    = 2000
BOOT_DELAY_MS         = 200

def _uid_to_hex(uid4):
    return "".join("{:02X}".format(b) for b in uid4)

def _init_reader():
    spi = SPI(
        SPI_ID,
        baudrate=5_000_000,
        polarity=0,
        phase=0,
        sck=Pin(PIN_SCK),
        mosi=Pin(PIN_MOSI),
        miso=Pin(PIN_MISO),
    )
    cs = Pin(PIN_CS, Pin.OUT, value=1)
    rst = Pin(PIN_RST, Pin.OUT, value=1)
    return MFRC522(spi, cs, rst)

def _read_uid_hex(rdr):
    stat, _ = rdr.request(rdr.PICC_REQIDL)
    if stat != rdr.OK:
        return None
    stat2, uid = rdr.anticoll()
    if stat2 != rdr.OK:
        return None
    return _uid_to_hex(uid).upper()

def run(local_ip=None, feed=None):
    rdr = _init_reader()
    spice_uid = SPICE_UID_HEX.upper()
    osc = OSCClient(DIRECTOR_IP, DIRECTOR_PORT)

    print("=== RFID ===")
    print("Pret. Attente epice stable (3s) -> demarrage.")
    print("Jeu: retrait > 3s -> utilisation. Repose -> reset direct.")

    state = "WAIT_STABLE"
    stable_start_ms = None

    last_seen_spice_ms = None
    absence_start_ms = None
    usage_sent = False

    last_wrong_uid = None
    last_log_ms = time.ticks_ms()

    last_present_sent = None

    start_ms = time.ticks_ms()
    last_alive_ms = 0
    boot_sent = False

    while True:
        if feed is not None:
            feed()

        now = time.ticks_ms()

        if (not boot_sent) and time.ticks_diff(now, start_ms) >= BOOT_DELAY_MS:
            boot_sent = True
            try:
                osc.send(
                    "/sys/boot",
                    ",iss",
                    SPICE_ID,
                    SPICE_NAME,
                    "" if local_ip is None else local_ip,
                )
            except:
                pass

        if time.ticks_diff(now, last_alive_ms) >= HEARTBEAT_EVERY_MS:
            last_alive_ms = now
            uptime_s = time.ticks_diff(now, start_ms) // 1000
            try:
                osc.send("/sys/alive", ",isi", SPICE_ID, SPICE_NAME, uptime_s)
            except:
                pass

        uid_hex = _read_uid_hex(rdr)

        if uid_hex == spice_uid:
            last_seen_spice_ms = now
        elif uid_hex is not None:
            if uid_hex != last_wrong_uid:
                print("badge INCORECT")
                last_wrong_uid = uid_hex
                try:
                    osc.send("/io/spice/wrong", ",is", SPICE_ID, uid_hex)
                except:
                    pass

        spice_present = (
            last_seen_spice_ms is not None
            and time.ticks_diff(now, last_seen_spice_ms) <= PRESENT_GRACE_MS
        )

        if last_present_sent is None or spice_present != last_present_sent:
            last_present_sent = spice_present
            try:
                osc.send("/io/spice", ",ii", SPICE_ID, 1 if spice_present else 0)
            except:
                pass

        if time.ticks_diff(now, last_log_ms) >= LOG_EVERY_MS:
            if state == "WAIT_STABLE":
                ms = 0 if stable_start_ms is None else time.ticks_diff(now, stable_start_ms)
                print("LOG: attente epice stable ({} ms)".format(ms))
            else:
                if spice_present:
                    print("LOG: {} PRESENT sur socle".format(SPICE_NAME))
                else:
                    if absence_start_ms is None:
                        print("LOG: {} ABSENT (timer pas demarre)".format(SPICE_NAME))
                    else:
                        ms = time.ticks_diff(now, absence_start_ms)
                        print("LOG: {} ABSENT depuis {} ms".format(SPICE_NAME, ms))
            last_log_ms = now

        if state == "WAIT_STABLE":
            if spice_present:
                if stable_start_ms is None:
                    stable_start_ms = now
                elif time.ticks_diff(now, stable_start_ms) >= START_STABLE_MS:
                    state = "ACTIVE"
                    absence_start_ms = None
                    usage_sent = False
                    print("Jeu demarre.")
                    try:
                        osc.send("/io/spice/ready", ",i", SPICE_ID)
                    except:
                        pass
            else:
                stable_start_ms = None

            time.sleep_ms(40)
            continue

        if spice_present:
            if absence_start_ms is not None:
                print("Epice reposee sur socle.")
            absence_start_ms = None
            usage_sent = False
        else:
            if absence_start_ms is None:
                absence_start_ms = now
                print("Retiree du socle (timer demarre).")
                usage_sent = False

            if (not usage_sent) and time.ticks_diff(now, absence_start_ms) >= ABSENCE_MS_TO_TRIGGER:
                print("utilisation de {}.".format(SPICE_NAME))
                usage_sent = True
                try:
                    osc.send("/io/spice/use", ",i", SPICE_ID)
                except:
                    pass

        time.sleep_ms(40)

