# director.py
import os
import time
import logging
from logging.handlers import RotatingFileHandler

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

import config
from state_spices import SpicesState
from state_spoon import SpoonsState


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


# ---- STATE ----
spices = SpicesState(spice_ids=(1, 2, 3, 4))
spoons = SpoonsState(target=3)


# ---- MadMapper (stub) ----
mm = SimpleUDPClient(config.MADMAPPER_IP, config.MADMAPPER_PORT)

def mm_base(cue_name: str):
    logging.info(f"{now_hms()} | MM     | base={cue_name}")

def mm_overlay(cue_name: str):
    logging.info(f"{now_hms()} | MM     | overlay={cue_name}")


# ---- DEBUG: log tout ce qui arrive ----
def on_any(client_addr, address, *args):
    ip, port = client_addr
    logging.info(f"{now_hms()} | RX     | from={ip}:{port} addr={address} args={args}")


# ---- OSC IN handlers épices ----
def on_spice(client_addr, address, spice_id, present):
    spice_id = int(spice_id)
    present = 1 if int(present) else 0

    if not spices.is_known(spice_id):
        ip, port = client_addr
        logging.info(f"{now_hms()} | WARN   | from={ip}:{port} unknown_spice={spice_id}")
        return

    changed = spices.set_present(spice_id, present)
    if changed:
        ip, port = client_addr
        action = "ON" if spices.present[spice_id] == 1 else "OFF"
        logging.info(f"{now_hms()} | SPICE  | id={spice_id} present={action} from={ip}:{port}")
        logging.info(f"{now_hms()} | STATE  | {spices.state_line()}")

def on_spice_use(client_addr, address, spice_id):
    spice_id = int(spice_id)

    if not spices.is_known(spice_id):
        ip, port = client_addr
        logging.info(f"{now_hms()} | WARN   | from={ip}:{port} unknown_spice={spice_id}")
        return

    spices.mark_use(spice_id)
    ip, port = client_addr
    logging.info(f"{now_hms()} | USE    | id={spice_id} from={ip}:{port}")
    logging.info(f"{now_hms()} | STATE  | {spices.state_line()}")

def on_spice_wrong(client_addr, address, spice_id, uid):
    ip, port = client_addr
    logging.info(f"{now_hms()} | WRONG  | id={int(spice_id)} uid={uid} from={ip}:{port}")

def on_ready(client_addr, address, spice_id):
    ip, port = client_addr
    logging.info(f"{now_hms()} | READY  | id={int(spice_id)} from={ip}:{port}")

def on_reset(client_addr, address, *args):
    spices.reset_used()
    logging.info(f"{now_hms()} | RESET  | {spices.state_line()}")


# ---- Heartbeat épices ----
def on_alive(client_addr, address, spice_id, spice_name, uptime_s):
    ip, port = client_addr
    logging.info(f"{now_hms()} | ALIVE  | id={int(spice_id)} name={spice_name} up={int(uptime_s)}s from={ip}:{port}")

def on_boot(client_addr, address, spice_id, spice_name, local_ip):
    ip, port = client_addr
    logging.info(f"{now_hms()} | BOOT   | id={int(spice_id)} name={spice_name} ip={local_ip} from={ip}:{port}")


# ---- Cuillère ----
def on_spoon_rot(client_addr, address, spoon_id, direction):
    ip, port = client_addr
    sid = int(spoon_id)
    d = int(direction)

    label = "DROITE" if d == 1 else ("GAUCHE" if d == -1 else "UNK")
    logging.info(f"{now_hms()} | SPOON  | rot={label} id={sid} from={ip}:{port}")

    done = spoons.get(sid).push(d)
    if done:
        done_label = "DROITE" if d == 1 else "GAUCHE"
        logging.info(f"{now_hms()} | SPOON  | DONE dir={done_label} id={sid}")

        # sortie OSC vers MadMapper (spoon_id, dir)
        try:
            mm.send_message("/io/spoon/done", [sid, d])
        except Exception as e:
            logging.info(f"{now_hms()} | MMERR  | {e}")

def on_spoon_alive(client_addr, address, spoon_id, uptime_s):
    ip, port = client_addr
    logging.info(f"{now_hms()} | SPOON  | ALIVE id={int(spoon_id)} up={int(uptime_s)}s from={ip}:{port}")

def on_spoon_boot(client_addr, address, spoon_id, local_ip):
    ip, port = client_addr
    logging.info(f"{now_hms()} | SPOON  | BOOT id={int(spoon_id)} ip={local_ip} from={ip}:{port}")


def main():
    setup_logging()

    disp = Dispatcher()
    disp.set_default_handler(on_any, needs_reply_address=True)

    # épices
    disp.map("/io/spice", on_spice, needs_reply_address=True)               # (id, present)
    disp.map("/io/spice/use", on_spice_use, needs_reply_address=True)       # (id)
    disp.map("/io/spice/wrong", on_spice_wrong, needs_reply_address=True)   # (id, uid)
    disp.map("/io/spice/ready", on_ready, needs_reply_address=True)         # (id)
    disp.map("/director/reset", on_reset, needs_reply_address=True)         # ()
    disp.map("/sys/alive", on_alive, needs_reply_address=True)              # (id, name, uptime_s)
    disp.map("/sys/boot", on_boot, needs_reply_address=True)                # (id, name, local_ip)

    # cuillère
    disp.map("/io/spoon/rot", on_spoon_rot, needs_reply_address=True)        # (spoon_id, dir)
    disp.map("/sys/spoon/alive", on_spoon_alive, needs_reply_address=True)   # (spoon_id, uptime_s)
    disp.map("/sys/spoon/boot", on_spoon_boot, needs_reply_address=True)     # (spoon_id, local_ip)

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
