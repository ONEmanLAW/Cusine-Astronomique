# game.py
import time
import threading
import logging
from enum import Enum, auto

import config

class GameState(Enum):
    BOOT = auto()
    TUTO = auto()
    TREMBLEMENT = auto()
    TRANS1 = auto()

    METEORITE = auto()
    LASER1 = auto()
    TRANS2 = auto()

    ALIEN = auto()
    LASER2 = auto()
    TRANS3 = auto()

    END = auto()

class Game:
    def __init__(self, mm):
        self.mm = mm

        self.state = GameState.BOOT

        self._main_timer = None
        self._pot_timer = None
        self._slot_timers = {}

        # tremblement counter (consécutif même direction)
        self.tremble_target = int(config.TREMBLE_STIR_N)
        self.tremble_last_dir = 0
        self.tremble_count = 0

        # combo (meteorite/alien)
        self.order = []
        self.order_idx = 0
        self.spices_done = False

        self.stir_dir_required = 0
        self.stir_target = 0
        self.stir_count = 0

        # lock pot pendant affichage couleur épice
        self.pot_locked_until = 0.0

    # ---------- timers ----------
    def _cancel(self, t):
        if t:
            t.cancel()
        return None

    def after(self, seconds: float, fn):
        self._main_timer = self._cancel(self._main_timer)
        t = threading.Timer(seconds, fn)
        t.daemon = True
        self._main_timer = t
        t.start()

    def pot_after(self, seconds: float, fn):
        self._pot_timer = self._cancel(self._pot_timer)
        t = threading.Timer(seconds, fn)
        t.daemon = True
        self._pot_timer = t
        t.start()

    def slot_after(self, slot: int, seconds: float, fn):
        old = self._slot_timers.get(slot)
        if old:
            old.cancel()
        t = threading.Timer(seconds, fn)
        t.daemon = True
        self._slot_timers[slot] = t
        t.start()

    # ---------- lifecycle ----------
    def start(self):
        self.mm.pot("IDLE")
        self.mm.clear_all_ovr()
        self.enter_tuto()

    def reset(self):
        self.start()

    # ---------- transitions ----------
    def enter_tuto(self):
        self.state = GameState.TUTO
        logging.info("GAME   | state=TUTO")
        self.mm.dash("TUTO")
        self.mm.pot("IDLE")
        self.after(config.DASH_TUTO_S, self.on_tuto_end)

    def on_tuto_end(self):
        if self.state != GameState.TUTO:
            return
        self.enter_tremblement()

    def enter_tremblement(self):
        self.state = GameState.TREMBLEMENT
        self.tremble_last_dir = 0
        self.tremble_count = 0
        logging.info(f"GAME   | state=TREMBLEMENT target={self.tremble_target}")
        self.mm.dash("TREMBLE")
        self.mm.pot("IDLE")

    def enter_trans1(self):
        self.state = GameState.TRANS1
        logging.info("GAME   | state=TRANS1")
        self.mm.dash("TRANS1")
        self.mm.pot("IDLE")
        self.after(config.DASH_TRANS1_S, self.on_trans1_end)

    def on_trans1_end(self):
        if self.state != GameState.TRANS1:
            return
        self.enter_meteorite()

    def enter_meteorite(self):
        self.state = GameState.METEORITE
        self.order = list(config.METEORITE_ORDER)
        self.order_idx = 0
        self.spices_done = False

        self.stir_dir_required = int(config.METEORITE_STIR_DIR)
        self.stir_target = int(config.METEORITE_STIR_N)
        self.stir_count = 0

        self.mm.clear_all_ovr()
        self.mm.dash("METEORI")
        self.mm.pot("IDLE")
        logging.info(f"GAME   | state=METEORITE order={self.order} stir={self.stir_target} dir={self.stir_dir_required}")

    def enter_laser1(self):
        self.state = GameState.LASER1
        logging.info("GAME   | state=LASER1")
        self.mm.dash("LASER1")
        self.mm.pot("IDLE")
        self.after(config.DASH_LASER1_S, self.on_laser1_end)

    def on_laser1_end(self):
        if self.state != GameState.LASER1:
            return
        self.enter_trans2()

    def enter_trans2(self):
        self.state = GameState.TRANS2
        logging.info("GAME   | state=TRANS2")
        self.mm.dash("TRANS2")
        self.mm.pot("IDLE")
        self.after(config.DASH_TRANS2_S, self.on_trans2_end)

    def on_trans2_end(self):
        if self.state != GameState.TRANS2:
            return
        self.enter_alien()

    def enter_alien(self):
        self.state = GameState.ALIEN
        self.order = list(config.ALIEN_ORDER)
        self.order_idx = 0
        self.spices_done = False

        self.stir_dir_required = int(config.ALIEN_STIR_DIR)
        self.stir_target = int(config.ALIEN_STIR_N)
        self.stir_count = 0

        self.mm.clear_all_ovr()
        self.mm.dash("ALIEN")
        self.mm.pot("IDLE")
        logging.info(f"GAME   | state=ALIEN order={self.order} stir={self.stir_target} dir={self.stir_dir_required}")

    def enter_laser2(self):
        self.state = GameState.LASER2
        logging.info("GAME   | state=LASER2")
        self.mm.dash("LASER2")
        self.mm.pot("IDLE")
        self.after(config.DASH_LASER2_S, self.on_laser2_end)

    def on_laser2_end(self):
        if self.state != GameState.LASER2:
            return
        self.enter_trans3()

    def enter_trans3(self):
        self.state = GameState.TRANS3
        logging.info("GAME   | state=TRANS3")
        self.mm.dash("TRANS3")
        self.mm.pot("IDLE")
        self.after(config.DASH_TRANS3_S, self.on_trans3_end)

    def on_trans3_end(self):
        if self.state != GameState.TRANS3:
            return
        self.enter_end()

    def enter_end(self):
        self.state = GameState.END
        logging.info("GAME   | state=END")
        self.mm.dash("END")
        self.mm.pot("IDLE")

    # ---------- inputs ----------
    def on_spice_use(self, spice_id: int):
        if self.state not in (GameState.METEORITE, GameState.ALIEN):
            return

        sid = int(spice_id)
        if sid not in (1, 2, 3, 4):
            return

        # pot couleur = toujours (même si faux)
        self.mm.pot(f"SPICE{sid}")
        self.pot_locked_until = time.time() + config.POT_SPICE_HOLD_S
        self.pot_after(config.POT_SPICE_HOLD_S, lambda: self.mm.pot("IDLE"))

        expected = self.order[self.order_idx] if self.order_idx < len(self.order) else None
        ok = (sid == expected)

        if ok:
            self.mm.ovr(sid, "good")
            self.slot_after(sid, config.OVR_SPICE_SHOW_S, lambda s=sid: self.mm.ovr(s, "clear"))

            self.order_idx += 1
            if self.order_idx >= len(self.order):
                self.spices_done = True
                self.stir_count = 0

            nxt = self.order[self.order_idx] if self.order_idx < len(self.order) else "DONE"
            logging.info(f"COMBO  | ok spice={sid} next={nxt} spices_done={self.spices_done}")
        else:
            # si réutilisé après validation -> ça doit rouge: donc jamais d'ignore
            self.mm.ovr(sid, "bad")
            self.slot_after(sid, config.OVR_SPICE_SHOW_S, lambda s=sid: self.mm.ovr(s, "clear"))
            logging.info(f"COMBO  | bad spice={sid} expected={expected}")

    def on_spoon_rot(self, direction: int):
        d = int(direction)
        if d not in (-1, 1):
            return

        # animation marmite one-shot, sauf si locked par pot_spice
        if time.time() >= self.pot_locked_until:
            if d == -1:
                self.mm.pot("LEFT")
            else:
                self.mm.pot("RIGHT")
            self.pot_after(config.POT_TURN_S, lambda: self.mm.pot("IDLE"))

        # tremblement: consécutif même sens, log 1/5 2/5 ...
        if self.state == GameState.TREMBLEMENT:
            if d == self.tremble_last_dir:
                self.tremble_count += 1
            else:
                self.tremble_last_dir = d
                self.tremble_count = 1

            lab = "GAUCHE" if d == -1 else "DROITE"
            logging.info(f"TREMBL | {self.tremble_count}/{self.tremble_target} dir={lab}")

            if self.tremble_count >= self.tremble_target:
                logging.info("TREMBL | DONE -> TRANS1")
                self.enter_trans1()
            return

        # combos: touillage final après épices
        if self.state in (GameState.METEORITE, GameState.ALIEN) and self.spices_done:
            if d == self.stir_dir_required:
                self.stir_count += 1
                logging.info(f"STIR   | {self.state.name} {self.stir_count}/{self.stir_target} dir=OK")
            else:
                # METEORITE: mauvais sens reset
                if self.state == GameState.METEORITE:
                    self.stir_count = 0
                    logging.info(f"STIR   | METEORITE wrong_dir -> reset 0/{self.stir_target}")
                # ALIEN: mauvais sens NE RETIRE RIEN
                else:
                    logging.info(f"STIR   | ALIEN wrong_dir -> ignore (reste {self.stir_count}/{self.stir_target})")

            if self.stir_count >= self.stir_target:
                if self.state == GameState.METEORITE:
                    self.enter_laser1()
                else:
                    self.enter_laser2()
