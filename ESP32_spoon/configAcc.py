DEVICE_ID = "stir_1"

# ===== Wi-Fi =====
WIFI_SSID = "xxxxx"
WIFI_PASSWORD = "xxxx"

# ===== OSC target (Mac) =====
OSC_TARGET_IP = "00.00.000.000" # Mettre bonne ip
OSC_TARGET_PORT = 8000 # Mettre bon port

# OSC addresses
OSC_ADDR_STATE = "/stir"        
OSC_ADDR_EVENT = "/stir/event" 

# Cadence
LOOP_PERIOD_MS = 25  # ~40 Hz
DEBUG_INTERVAL_MS = 300
PRINT_I2C_SCAN = True

# ===== I2C / MPU6050 =====
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ_HZ = 100000
MPU_CANDIDATES = (0x68, 0x69)

# ===== Détection touillage (accéléro) =====
# Plus petit = plus sensible
LATERAL_START_G = 0.03
LATERAL_STOP_G  = 0.02
LATERAL_MIN_FOR_ANGLE_G = 0.025

# Tour complet
TOUR_SEUIL_DEG = 360.0
MAX_PAUSE_MS = 500

# Contrainte amplitude (plus petit = plus facile, plus grand = exige gros rond)
ENERGIE_LATERALE_MIN = 8.0

# Filtres
GRAVITY_ALPHA = 0.02
LATERAL_ALPHA = 0.35

# Droite / Gauche (si inversé: -1)
DROITE_GAUCHE_SIGN = -1
