import time

class SpicesState:

    def __init__(self, spice_ids=(1, 2, 3, 4)):
        self.spice_ids = tuple(spice_ids)
        self.present = {i: 0 for i in self.spice_ids}
        self.used = {i: False for i in self.spice_ids}
        self.last_use_ts = {i: 0.0 for i in self.spice_ids}

    def reset_used(self):
        for i in self.spice_ids:
            self.used[i] = False
            self.last_use_ts[i] = 0.0

    def is_known(self, spice_id: int) -> bool:
        return spice_id in self.present

    def set_present(self, spice_id: int, present: int) -> bool:
        present = 1 if int(present) else 0
        prev = self.present[spice_id]
        self.present[spice_id] = present
        return prev != present

    def mark_use(self, spice_id: int):
        self.used[spice_id] = True
        self.last_use_ts[spice_id] = time.time()

    def state_line(self) -> str:
        p = " ".join([f"{i}:{self.present[i]}" for i in self.spice_ids])
        u = " ".join([f"{i}:{'T' if self.used[i] else 'F'}" for i in self.spice_ids])
        return f"P[{p}]  U[{u}]"
