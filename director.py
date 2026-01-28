import os
import time
import logging
from logging.handlers import RotatingFileHandler

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

import config


# ----------------- LOGGING -----------------
def setup_logging():
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    fh = RotatingFileHandler("logs/director.log", maxBytes=500_000, backupCount=3)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)


# ----------------- GAME STATE (minimal) -----------------
spice_present = {1: 0, 2: 0, 3: 0, 4: 0}
last_use_ts = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}


# ----------------- MADMAPPER OUT (stub) -----------------
mm = SimpleUDPClient(config.MADMAPPER_IP, config.MADMAPPER_PORT)

def mm_base(cue_name: str):
    # à activer quand MadMapper est prêt
    # mm.send_message("/mm/base", cue_name)
    logging.info(f"MM OUT /mm/base {cue_name}")

def mm_overlay(cue_name: str):
    # mm.send_message("/mm/overlay", cue_name)
    logging.info(f"MM OUT /mm/overlay {cue_name}")

def mm_wrong_spice(spice_id: int):
    # mm.send_message("/mm/trig/wrong_spice", spice_id)
    logging.info(f"MM OUT /mm/trig/wrong_spice {spice_id}")


# ----------------- OSC IN HANDLERS -----------------
def on_spice(addr, spice_id, present):
    spice_id = int(spice_id)
    present = int(present)

    if spice_id not in spice_present:
        logging.warning(f"{addr} unknown spice_id={spice_id}")
        return

    prev = spice_present[spice_id]
    spice_present[spice_id] = present

    if prev != present:
        logging.info(f"{addr} /io/spice spice={spice_id} present={present}")

def on_spice_use(addr, spice_id):
    spice_id = int(spice_id)
    if spice_id not in spice_present:
        logging.warning(f"{addr} unknown spice_id={spice_id}")
        return

    now = time.time()
    last_use_ts[spice_id] = now
    logging.info(f"{addr} /io/spice/use spice={spice_id} USE")

    # Exemple: feedback MadMapper (plus tard)
    # mm_overlay("spice_used_fx")

def on_spice_wrong(addr, spice_id, uid):
    spice_id = int(spice_id)
    logging.info(f"{addr} /io/spice/wrong spice={spice_id} uid={uid}")

    # Exemple: trigger overlay erreur
    # mm_wrong_spice(spice_id)

def on_ready(addr, spice_id):
    spice_id = int(spice_id)
    logging.info(f"{addr} /io/spice/ready spice={spice_id} READY")


def main():
    setup_logging()

    disp = Dispatcher()
    disp.map("/io/spice", on_spice)              # (id, present)
    disp.map("/io/spice/use", on_spice_use)      # (id)
    disp.map("/io/spice/wrong", on_spice_wrong)  # (id, uid_str)
    disp.map("/io/spice/ready", on_ready)        # (id)

    server = ThreadingOSCUDPServer(
        (config.DIRECTOR_LISTEN_IP, config.DIRECTOR_LISTEN_PORT),
        disp
    )

    ip, port = server.server_address
    logging.info(f"Director listening OSC UDP on {ip}:{port}")

    server.serve_forever()


if __name__ == "__main__":
    main()
