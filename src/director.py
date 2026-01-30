# director.py
import os
import time
import sys
import threading
import select
import termios
import tty
import logging
from logging.handlers import RotatingFileHandler

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

import config
from mm_client import MM
from game import Game
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


# juste pour logs présence épices (si tu l'utilises encore)
spices_state = SpicesState(spice_ids=(1, 2, 3, 4))

mm = MM(config.MADMAPPER_IP, config.MADMAPPER_PORT)
game = Game(mm)


def on_any(client_addr, address, *args):
    ip, port = client_addr
    logging.info(f"RX     | from={ip}:{port} addr={address} args={args}")


def on_spice_present(client_addr, address, spice_id, present):
    sid = int(spice_id)
    p = 1 if int(present) else 0
    if not spices_state.is_known(sid):
        ip, port = client_addr
        logging.info(f"WARN   | from={ip}:{port} unknown_spice={sid}")
        return
    changed = spices_state.set_present(sid, p)
    if changed:
        action = "ON" if p == 1 else "OFF"
        logging.info(f"SPICE  | present id={sid} {action}")
        logging.info(f"STATE  | {spices_state.state_line()}")


def on_spice_use(client_addr, address, spice_id):
    sid = int(spice_id)
    ip, port = client_addr
    logging.info(f"USE    | id={sid} from={ip}:{port}")
    game.on_spice_use(sid)


def on_spoon_rot(client_addr, address, spoon_id, direction):
    sid = int(spoon_id)
    d = int(direction)
    ip, port = client_addr
    lab = "DROITE" if d == 1 else ("GAUCHE" if d == -1 else "UNK")
    logging.info(f"SPOON  | rot={lab} id={sid} from={ip}:{port}")
    game.on_spoon_rot(d)


def on_start(client_addr, address, *args):
    ip, port = client_addr
    logging.info(f"START  | from={ip}:{port} -> game.on_start()")
    game.on_start()


def on_reset(client_addr, address, *args):
    spices_state.reset_used()
    logging.info(f"RESET  | {spices_state.state_line()}")
    game.reset()


def start_keyboard_sim():
    def loop():
        logging.info("KBD    | ON ($=start a=gauche d=droite 1-4=spice_use r=reset)")
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        try:
            while True:
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not r:
                    continue
                ch = sys.stdin.read(1)
                if not ch:
                    continue
                c = ch.lower()

                if c == "$":
                    game.on_start()
                elif c == "a":
                    game.on_spoon_rot(-1)
                elif c == "d":
                    game.on_spoon_rot(1)
                elif c in ("1", "2", "3", "4"):
                    game.on_spice_use(int(c))
                elif c == "r":
                    game.reset()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    t = threading.Thread(target=loop, daemon=True)
    t.start()


def main():
    setup_logging()

    disp = Dispatcher()
    disp.set_default_handler(on_any, needs_reply_address=True)

    disp.map("/io/spice", on_spice_present, needs_reply_address=True)        # (id, present)
    disp.map("/io/spice/use", on_spice_use, needs_reply_address=True)        # (id)
    disp.map("/io/spoon/rot", on_spoon_rot, needs_reply_address=True)        # (spoon_id, dir)

    disp.map("/director/start", on_start, needs_reply_address=True)          # ()
    disp.map("/director/reset", on_reset, needs_reply_address=True)          # ()

    server = ThreadingOSCUDPServer(
        (config.DIRECTOR_LISTEN_IP, config.DIRECTOR_LISTEN_PORT),
        disp
    )

    ip, port = server.server_address
    logging.info(f"START  | listening={ip}:{port}")

    if getattr(config, "DEV_KEYBOARD", False):
        start_keyboard_sim()

    game.start()
    server.serve_forever()


if __name__ == "__main__":
    main()
