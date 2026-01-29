# state_spoon.py

class SpoonCounter:
    def __init__(self, target=3):
        self.target = int(target)
        self.last_dir = 0
        self.count = 0

    def reset(self):
        self.last_dir = 0
        self.count = 0

    def push(self, direction: int) -> bool:
        d = int(direction)
        if d not in (-1, 1):
            return False

        if d == self.last_dir:
            self.count += 1
        else:
            self.last_dir = d
            self.count = 1

        if self.count >= self.target:
            self.reset()
            return True
        return False


class SpoonsState:
    def __init__(self, target=3):
        self.target = int(target)
        self._spoons = {}  # spoon_id -> SpoonCounter

    def get(self, spoon_id: int) -> SpoonCounter:
        sid = int(spoon_id)
        if sid not in self._spoons:
            self._spoons[sid] = SpoonCounter(target=self.target)
        return self._spoons[sid]

    def reset(self, spoon_id: int = None):
        if spoon_id is None:
            for c in self._spoons.values():
                c.reset()
        else:
            sid = int(spoon_id)
            if sid in self._spoons:
                self._spoons[sid].reset()
