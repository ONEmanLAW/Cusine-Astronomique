# Reçoit le message OSC envoyé par MadMapper: /mm/tuto/done 1

import logging
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 1234
ADDR_DONE = "/mm/tuto/done"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

def on_done(address, value):
    logging.info(f"RECEIVED {address} {value}")

def on_any(address, *args):
    logging.info(f"IN {address} args={args}")

disp = Dispatcher()
disp.map(ADDR_DONE, on_done)
disp.set_default_handler(on_any) 

server = ThreadingOSCUDPServer((LISTEN_IP, LISTEN_PORT), disp)
logging.info(f"Listening UDP {LISTEN_IP}:{LISTEN_PORT}")
server.serve_forever()
