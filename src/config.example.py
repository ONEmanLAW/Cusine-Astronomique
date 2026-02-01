# config.example.py

DIRECTOR_LISTEN_IP = "0.0.0.0"
DIRECTOR_LISTEN_PORT = 1234

MADMAPPER_IP = "127.0.0.1" # Mettre bonne ip
MADMAPPER_PORT = 8000 # Mettre bon port

# DEV clavier
DEV_KEYBOARD = True
DEV_SPOON_ID = 1

# Durées vidéos (secondes)
DASH_TUTO_S   = 48
DASH_TRANS1_S = 5
DASH_LASER1_S = 6.6
DASH_TRANS2_S = 4.4
DASH_LASER2_S = 6.80


DASH_TRANS3_S = 15.0

# Marmite left/right = one-shot puis retour idle
POT_TURN_S = 2

# Marmite couleur épice
POT_SPICE_HOLD_S = 10

# Overlay épices (vert/rouge)
OVR_SPICE_SHOW_S = 6.0

# Tremblement: nombre de tours consécutifs même sens
TREMBLE_STIR_N = 3

# Meteorite: ordre + touillage final
METEORITE_ORDER = (4, 1, 2, 3)
METEORITE_STIR_DIR = 1    # +1 droite
METEORITE_STIR_N   = 3

# Alien: ordre + touillage final
ALIEN_ORDER = (4, 3, 2, 1)
ALIEN_STIR_DIR = -1       # -1 gauche
ALIEN_STIR_N   = 3
