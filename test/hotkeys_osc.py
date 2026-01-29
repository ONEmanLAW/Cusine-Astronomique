# hotkeys_osc.py
# Hotkeys clavier -> OSC (simulate ESP32 + test MadMapper)


from pythonosc.udp_client import SimpleUDPClient
from pynput import keyboard # pyright: ignore[reportMissingModuleSource]
import time

# ---------- Réseau ----------
DIRECTOR_IP = "127.0.0.1"
DIRECTOR_PORT = 1234

MADMAPPER_IP = "10.37.221.146"
MADMAPPER_PORT = 8000

director = SimpleUDPClient(DIRECTOR_IP, DIRECTOR_PORT)
mm = SimpleUDPClient(MADMAPPER_IP, MADMAPPER_PORT)

SPOON_ID = 1

# ---------- Helpers ----------
def send_director(addr, args=None):
    if args is None:
        args = []
    director.send_message(addr, args)
    print(f"[TX -> DIRECTOR] {addr} {args}")

def send_mm(addr, args=None):
    if args is None:
        args = 1
    mm.send_message(addr, args)
    print(f"[TX -> MM] {addr} {args}")

# ---------- Etat local pour toggles ----------
present = {1: 0, 2: 0, 3: 0, 4: 0}

def toggle_present(spice_id: int):
    present[spice_id] = 0 if present[spice_id] == 1 else 1
    send_director("/io/spice", [spice_id, present[spice_id]])

# ---------- Mapping Hotkeys ----------
# Simulation ESP32 -> Director
def spoon_left():
    send_director("/io/spoon/rot", [SPOON_ID, -1])

def spoon_right():
    send_director("/io/spoon/rot", [SPOON_ID, 1])

def spice_use(i):
    send_director("/io/spice/use", [i])

def reset_director():
    send_director("/director/reset", [])

# Test direct MadMapper -> (tes controls custom)
MM_ADDR = {
    "tuto":      "/mm/dash/tuto",
    "tremble":   "/mm/dash/tremble",
    "trans1":    "/mm/dash/trans1",
    "meteorite": "/mm/dash/meteorite",

    "pot_idle":  "/mm/pot/idle",
    "pot_left":  "/mm/pot/left",
    "pot_right": "/mm/pot/right",

    "slot1_good":  "/mm/ovr/slot1/good",
    "slot1_bad":   "/mm/ovr/slot1/bad",
    "slot1_clear": "/mm/ovr/slot1/clear",

    "slot2_good":  "/mm/ovr/slot2/good",
    "slot2_bad":   "/mm/ovr/slot2/bad",
    "slot2_clear": "/mm/ovr/slot2/clear",

    "slot3_good":  "/mm/ovr/slot3/good",
    "slot3_bad":   "/mm/ovr/slot3/bad",
    "slot3_clear": "/mm/ovr/slot3/clear",

    "slot4_good":  "/mm/ovr/slot4/good",
    "slot4_bad":   "/mm/ovr/slot4/bad",
    "slot4_clear": "/mm/ovr/slot4/clear",
}

def mm_trigger(name):
    send_mm(MM_ADDR[name], 1)

# ---------- Hotkey handler ----------
def on_press(key):
    try:
        # ----- touches simples -----
        if key == keyboard.Key.left:
            spoon_left()                 # simule touillage gauche
        elif key == keyboard.Key.right:
            spoon_right()                # simule touillage droite

        elif hasattr(key, "char") and key.char:
            c = key.char.lower()

            # chiffres: usage épices (simulate /io/spice/use)
            if c in ("1", "2", "3", "4"):
                spice_use(int(c))

            # a/s/d/f: toggle présence épices (simulate /io/spice id present)
            elif c == "a":
                toggle_present(1)
            elif c == "s":
                toggle_present(2)
            elif c == "d":
                toggle_present(3)
            elif c == "f":
                toggle_present(4)

            # r: reset director
            elif c == "r":
                reset_director()

            # ----- tests MadMapper directs -----
            # t = tuto, y = tremble, u = trans1, i = meteorite
            elif c == "t":
                mm_trigger("tuto")
            elif c == "y":
                mm_trigger("tremble")
            elif c == "u":
                mm_trigger("trans1")
            elif c == "i":
                mm_trigger("meteorite")

            # j/k/l = pot left/idle/right
            elif c == "j":
                mm_trigger("pot_left")
            elif c == "k":
                mm_trigger("pot_idle")
            elif c == "l":
                mm_trigger("pot_right")

            # overlays slots: z/x/c/v = good, shift+... = bad, b = clear all
            elif c == "z":
                mm_trigger("slot1_good")
            elif c == "x":
                mm_trigger("slot2_good")
            elif c == "c":
                mm_trigger("slot3_good")
            elif c == "v":
                mm_trigger("slot4_good")
            elif c == "b":
                mm_trigger("slot1_clear"); mm_trigger("slot2_clear"); mm_trigger("slot3_clear"); mm_trigger("slot4_clear")

    except Exception as e:
        print("ERR:", e)

def on_release(key):
    # ESC = stop
    if key == keyboard.Key.esc:
        print("STOP")
        return False

def main():
    print("HOTKEYS ON")
    print("Director sim:")
    print("  <- / -> : /io/spoon/rot (id=1, dir=-1/+1)")
    print("  1..4    : /io/spice/use (id)")
    print("  a/s/d/f : toggle /io/spice (id present)")
    print("  r       : /director/reset")
    print("MadMapper direct:")
    print("  t tuto | y tremble | u trans1 | i meteorite")
    print("  j pot_left | k pot_idle | l pot_right")
    print("  z/x/c/v slot1..4 good | b clear all slots")
    print("ESC to quit")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
