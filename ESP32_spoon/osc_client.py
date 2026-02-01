import socket
import struct

def _pad4(b: bytes) -> bytes:
    n = (4 - (len(b) % 4)) % 4
    return b + (b"\x00" * n)

def _osc_str(s: str) -> bytes:
    return _pad4(s.encode("utf-8") + b"\x00")

def _osc_tags(args) -> str:
    t = ","
    for a in args:
        if isinstance(a, int):
            t += "i"
        else:
            t += "f"
    return t

def _osc_args(args) -> bytes:
    out = b""
    for a in args:
        if isinstance(a, int):
            out += struct.pack(">i", a)
        else:
            out += struct.pack(">f", float(a))
    return out

class OSCClient:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, address: str, *args):
        msg = _osc_str(address)
        msg += _osc_str(_osc_tags(args))
        msg += _osc_args(args)
        self.sock.sendto(msg, (self.ip, self.port))
