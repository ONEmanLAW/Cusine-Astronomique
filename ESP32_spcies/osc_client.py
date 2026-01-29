import usocket as socket # pyright: ignore[reportMissingImports]
import ustruct as struct # pyright: ignore[reportMissingImports]

def _pad4(n):
    return (4 - (n % 4)) % 4

def _osc_str(s):
    b = s.encode("utf-8") + b"\x00"
    b += b"\x00" * _pad4(len(b))
    return b

def _osc_i(i):
    return struct.pack(">i", int(i))

def build_message(address, typetags, args):
    msg = _osc_str(address) + _osc_str(typetags)
    for t, a in zip(typetags[1:], args):
        if t == "i":
            msg += _osc_i(a)
        elif t == "s":
            msg += _osc_str(a)
        else:
            raise ValueError("Unsupported OSC type: " + t)
    return msg

class OSCClient:
    def __init__(self, ip, port):
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, address, typetags, *args):
        pkt = build_message(address, typetags, args)
        self.sock.sendto(pkt, self.addr)



