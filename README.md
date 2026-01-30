# Cusine-ASTRONOMIQUE — Director (OSC)

### Description
- Serveur “Director” en Python
- Reçoit des messages OSC (ESP32 ou clavier)
- Pilote MadMapper via OSC (changement de vidéos / overlays)

### Prérequis
- macOS / Linux
- Python 3.10+ recommandé
- MadMapper configuré avec les adresses OSC /mm/...

Vérifier Python :
- python3 --version

### Installation des dépendances
Installer python-osc :
- python3 -m pip install python-osc

Si pip n’est pas dispo :
- python3 -m ensurepip --upgrade
- python3 -m pip install --upgrade pip
- python3 -m pip install python-osc

### Configuration
Éditer src/config.py :
- MADMAPPER_IP
- MADMAPPER_PORT
- Durées vidéo (DASH_*_S)
- Paramètres de jeu (ordre épices, nombre de tours, etc.)

### Lancer le Director
Depuis la racine du projet :
- python3 src/director.py

Logs :
- Console
- logs/director.log

### Contrôles clavier (mode test)
Activé si DEV_KEYBOARD = True dans src/config.py

Touches :
- a : cuillère gauche
- d : cuillère droite
- 1 2 3 4 : épices 1..4 (équivalent /io/spice/use)
- r : reset du jeu (revient au début)

### OSC (ESP32)
Le Director écoute sur :
- IP: DIRECTOR_LISTEN_IP (par défaut 0.0.0.0)
- Port: DIRECTOR_LISTEN_PORT (par défaut 1234)

Adresses attendues :
- /io/spoon/rot -> (spoon_id, dir) avec dir ∈ {-1, 1}
- /io/spice/use -> (spice_id) avec spice_id ∈ {1, 2, 3, 4}
- /director/reset -> ()

### Dépannage rapide

Python/pip introuvable :
- utiliser python3 et python3 -m pip
- python3 -m pip install python-osc
- python3 src/director.py

OSC mauvais overlay dans MadMapper :
- vérifier les Controls OSC dans MadMapper
- chaque adresse /mm/ovr/slotX/... doit être unique
- chaque adresse doit déclencher le bon cue (slot2 vs slot3, etc.)
