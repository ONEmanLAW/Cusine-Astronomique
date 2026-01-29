# config.example.py

DIRECTOR_LISTEN_IP = "0.0.0.0"
DIRECTOR_LISTEN_PORT = 1234

MADMAPPER_IP = "127.0.0.1"
MADMAPPER_PORT = 8000

# DEV clavier
DEV_KEYBOARD = True
DEV_SPOON_ID = 1

# Durées vidéos (secondes)
DASH_TUTO_S   = 25.0
DASH_TRANS1_S = 15.0
DASH_LASER1_S = 5.0
DASH_TRANS2_S = 15.0
DASH_LASER2_S = 5.0
DASH_TRANS3_S = 15.0

# Marmite left/right = one-shot puis retour idle
POT_TURN_S = 5

# Marmite couleur épice
POT_SPICE_HOLD_S = 10

# Overlay épices (vert/rouge)
OVR_SPICE_SHOW_S = 5.0

# Tremblement: nombre de tours consécutifs même sens
TREMBLE_STIR_N = 5

# Meteorite: ordre + touillage final
METEORITE_ORDER = (1, 2, 3, 4)
METEORITE_STIR_DIR = 1    # +1 droite
METEORITE_STIR_N   = 5

# Alien: ordre + touillage final
ALIEN_ORDER = (4, 3, 2, 1)
ALIEN_STIR_DIR = -1       # -1 gauche
ALIEN_STIR_N   = 5
