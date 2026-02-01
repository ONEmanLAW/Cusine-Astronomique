# Director OSC - Comment Lancer le projet

## Prérequis
- Un dossier projet contenant `server` avec les fichiers dedans
- Python installé (3.11+)

---

## Windows (PowerShell)

- Installer Python
  - `winget install -e --id Python.Python.3.12`

- Ouvrir un nouveau PowerShell, vérifier
  - `python --version`

- Aller dans le dossier projet
  - `cd "C:\chemin\vers\ton_projet"`

- Créer l’environnement virtuel + activer
  - `python -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1`

- Installer les dépendances
  - `python -m pip install --upgrade pip`
  - `python -m pip install python-osc`

- Lancer le serveur
  - `python director.py`

- Si aucun message ne remonte (firewall UDP 1234)
  - `netsh advfirewall firewall add rule name="Director OSC UDP 1234" dir=in action=allow protocol=UDP localport=1234`

---

## macOS (Terminal)

- Installer Python (Homebrew)
  - `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
  - `brew install python`

- Vérifier
  - `python3 --version`

- Aller dans le dossier projet
  - `cd "/chemin/vers/ton_projet"`

- Créer l’environnement virtuel + activer
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`

- Installer les dépendances
  - `python -m pip install --upgrade pip`
  - `python -m pip install python-osc`

- Lancer le serveur
  - `python director.py`

---

## Config réseau minimale
- `config.py` côté Director :
  - `DIRECTOR_LISTEN_IP = "0.0.0.0"`
  - `DIRECTOR_LISTEN_PORT = 8000`
- Les ESP32 doivent envoyer vers **l’IP du PC Director** sur le port **DIRECTOR_LISTEN_PORT**
- MadMapper écoute sur `MADMAPPER_IP` + `MADMAPPER_PORT`
