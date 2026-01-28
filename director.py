import os
import time
import logging
from logging.handlers import RotatingFileHandler

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

import config
from state_spices import SpicesState


def setup_logging():
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    fh = RotatingFileHandler("logs/director.log", maxBytes=500_000, backupCount=3)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)


def now_hms():
    t = time.localtime()
    return f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"


# ---- STATE (isolé dans un module) ----
spices = SpicesState(spice_ids=(1, 2, 3, 4))


# ---- MadMapper (stub) ----
mm = SimpleUDPClient(config.MADMAPPER_IP, config.MADMAPPER_PORT)

def mm_base(cue_name: str):
    # mm.send_message("/mm/base", cue_name)
    logging.info(f"{now_hms()} | MM     | base={cue_name}")

def mm_overlay(cue_name: str):
    # mm.send_message("/mm/overlay", cue_name)
    logging.info(f"{now_hms()} | MM     | overlay={cue_name}")


# ---- OSC IN handlers ----
def on_spice(addr, spice_id, present):
    spice_id = int(spice_id)
    present = int(present)

    if not spices.is_known(spice_id):
        logging.info(f"{now_hms()} | WARN   | {addr} unknown_spice={spice_id}")
        return

    changed = spices.set_present(spice_id, present)
    if changed:
        action = "ON" if spices.present[spice_id] == 1 else "OFF"
        logging.info(f"{now_hms()} | SPICE  | id={spice_id} present={action} from={addr}")
        logging.info(f"{now_hms()} | STATE  | {spices.state_line()}")

def on_spice_use(addr, spice_id):
    spice_id = int(spice_id)

    if not spices.is_known(spice_id):
        logging.info(f"{now_hms()} | WARN   | {addr} unknown_spice={spice_id}")
        return

    spices.mark_use(spice_id)
    logging.info(f"{now_hms()} | USE    | id={spice_id} from={addr}")
    logging.info(f"{now_hms()} | STATE  | {spices.state_line()}")

def on_spice_wrong(addr, spice_id, uid):
    logging.info(f"{now_hms()} | WRONG  | id={int(spice_id)} uid={uid} from={addr}")

def on_ready(addr, spice_id):
    logging.info(f"{now_hms()} | READY  | id={int(spice_id)} from={addr}")

def on_reset(addr, *args):
    spices.reset_used()
    logging.info(f"{now_hms()} | RESET  | {spices.state_line()}")


def main():
    setup_logging()

    disp = Dispatcher()
    disp.map("/io/spice", on_spice)               # (id, present)
    disp.map("/io/spice/use", on_spice_use)       # (id)
    disp.map("/io/spice/wrong", on_spice_wrong)   # (id, uid)
    disp.map("/io/spice/ready", on_ready)         # (id)
    disp.map("/director/reset", on_reset)         # ()

    server = ThreadingOSCUDPServer(
        (config.DIRECTOR_LISTEN_IP, config.DIRECTOR_LISTEN_PORT),
        disp
    )

    ip, port = server.server_address
    logging.info(f"{now_hms()} | START  | listening={ip}:{port}")
    logging.info(f"{now_hms()} | STATE  | {spices.state_line()}")

    server.serve_forever()


if __name__ == "__main__":
    main()
