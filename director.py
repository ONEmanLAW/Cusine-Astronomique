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


# ----------------- GAME STATE -----------------
spice_present = {1: 0, 2: 0, 3: 0, 4: 0}
spice_used    = {1: False, 2: False, 3: False, 4: False}
last_use_ts   = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}


def state_line():
    # Exemple: P[1:1 2:0 3:0 4:0]  U[1:T 2:F 3:F 4:F]
    p = " ".join([f"{i}:{spice_present[i]}" for i in (1,2,3,4)])
    u = " ".join([f"{i}:{'T' if spice_used[i] else 'F'}" for i in (1,2,3,4)])
    return f"P[{p}]  U[{u}]"


def reset_spice_used():
    for i in spice_used:
        spice_used[i] = False
        last_use_ts[i] = 0.0
    logging.info(f"{now_hms()} | RESET  | {state_line()}")


# ----------------- MADMAPPER OUT (stub) -----------------
mm = SimpleUDPClient(config.MADMAPPER_IP, config.MADMAPPER_PORT)

def mm_base(cue_name: str):
    # mm.send_message("/mm/base", cue_name)
    logging.info(f"{now_hms()} | MM     | base={cue_name}")

def mm_overlay(cue_name: str):
    # mm.send_message("/mm/overlay", cue_name)
    logging.info(f"{now_hms()} | MM     | overlay={cue_name}")

def mm_wrong_spice(spice_id: int):
    # mm.send_message("/mm/trig/wrong_spice", spice_id)
    logging.info(f"{now_hms()} | MM     | wrong_spice={spice_id}")


# ----------------- OSC IN HANDLERS -----------------
def on_spice(addr, spice_id, present):
    spice_id = int(spice_id)
    present = int(present)

    if spice_id not in spice_present:
        logging.info(f"{now_hms()} | WARN   | {addr} unknown_spice={spice_id}")
        return

    prev = spice_present[spice_id]
    spice_present[spice_id] = present

    # log seulement si changement
    if prev != present:
        action = "ON " if present == 1 else "OFF"
        logging.info(f"{now_hms()} | SPICE  | id={spice_id} present={action}  from={addr}")
        logging.info(f"{now_hms()} | STATE  | {state_line()}")

def on_spice_use(addr, spice_id):
    spice_id = int(spice_id)

    if spice_id not in spice_used:
        logging.info(f"{now_hms()} | WARN   | {addr} unknown_spice={spice_id}")
        return

    spice_used[spice_id] = True
    last_use_ts[spice_id] = time.time()

    logging.info(f"{now_hms()} | USE    | id={spice_id}  from={addr}")
    logging.info(f"{now_hms()} | STATE  | {state_line()}")

def on_spice_wrong(addr, spice_id, uid):
    spice_id = int(spice_id)
    logging.info(f"{now_hms()} | WRONG  | id={spice_id} uid={uid}  from={addr}")

def on_ready(addr, spice_id):
    spice_id = int(spice_id)
    logging.info(f"{now_hms()} | READY  | id={spice_id}  from={addr}")

def on_reset(addr, *args):
    reset_spice_used()


def main():
    setup_logging()

    disp = Dispatcher()
    disp.map("/io/spice", on_spice)
    disp.map("/io/spice/use", on_spice_use)
    disp.map("/io/spice/wrong", on_spice_wrong)
    disp.map("/io/spice/ready", on_ready)
    disp.map("/director/reset", on_reset)

    server = ThreadingOSCUDPServer(
        (config.DIRECTOR_LISTEN_IP, config.DIRECTOR_LISTEN_PORT),
        disp
    )

    ip, port = server.server_address
    logging.info(f"{now_hms()} | START  | listening={ip}:{port}")
    logging.info(f"{now_hms()} | STATE  | {state_line()}")

    server.serve_forever()


if __name__ == "__main__":
    main()
