"""
Random placement baseline.
"""

import random
import time
import copy
from .base import BasePlacer


class RandomPlacer(BasePlacer):
    name = "Random"

    def place(self, chip: dict, iterations: int = None) -> dict:
        t0 = time.time()
        random.seed(iterations or 42)
        new_chip = copy.deepcopy(chip)
        for c in new_chip["components"]:
            new_chip["components"][c] = {
                "x": random.randint(chip["die"]["x1"], chip["die"]["x2"]),
                "y": random.randint(chip["die"]["y1"], chip["die"]["y2"]),
            }
        hpwl = self._compute_hpwl(new_chip)
        return {
            "algorithm": self.name,
            "components": new_chip["components"],
            "hpwl": hpwl,
            "time": time.time() - t0,
        }
