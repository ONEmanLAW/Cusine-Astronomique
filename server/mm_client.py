# mm_client.py
import logging
from pythonosc.udp_client import SimpleUDPClient
from mm_routes import DASH, POT, OVR

class MM:
    def __init__(self, ip: str, port: int):
        self.client = SimpleUDPClient(ip, port)

    def send(self, addr: str, value=1, tag=""):
        try:
            self.client.send_message(addr, value)
            logging.info(f"MM_TX  | {tag} {addr} {value}")
        except Exception as e:
            logging.info(f"MMERR  | {e}")

    def dash(self, key: str):
        addr = DASH.get(key)
        if not addr:
            logging.info(f"MMWARN | DASH missing key={key}")
            return
        self.send(addr, 1, tag=f"DASH:{key}")

    def pot(self, key: str):
        addr = POT.get(key)
        if not addr:
            logging.info(f"MMWARN | POT missing key={key}")
            return
        self.send(addr, 1, tag=f"POT:{key}")

    def ovr(self, spice_id: int, kind: str):
        sid = int(spice_id)
        k = str(kind)
        addr = OVR.get(sid, {}).get(k)
        if not addr:
            logging.info(f"MMWARN | OVR missing spice={sid} kind={k}")
            return
        self.send(addr, 1, tag=f"OVR:spice={sid} kind={k}")

    def clear_all_ovr(self):
        for sid in (1, 2, 3, 4):
            self.ovr(sid, "clear")
