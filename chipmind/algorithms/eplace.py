"""
ePlace-style continuous relaxation placer.

Treats placement as a continuous optimization problem.
Minimizes weighted sum of squared wirelengths using gradient descent.
"""

import math
import time
import copy
from .base import BasePlacer


class EPlace(BasePlacer):
    name = "ePlace (gradient)"

    def __init__(self, iterations: int = 2000, lr: float = 0.1, **kwargs):
        super().__init__(**kwargs)
        self.iterations = iterations
        self.lr = lr

    def place(self, chip: dict, iterations: int = None) -> dict:
        t0 = time.time()
        iters = iterations or self.iterations
        die = chip["die"]
        die_w = die["x2"] - die["x1"]
        die_h = die["y2"] - die["y1"]

        # Initialize with random positions in normalized [0, 1]
        import random
        cell_names = list(chip["components"].keys())
        pos = {c: [random.random(), random.random()] for c in cell_names}

        def hpwl_norm():
            total = 0.0
            for net in chip["nets"]:
                if len(net["components"]) < 2:
                    continue
                cells = [c for c in net["components"] if c in pos]
                if len(cells) < 2:
                    continue
                xs = [pos[c][0] for c in cells]
                ys = [pos[c][1] for c in cells]
                total += (max(xs) - min(xs)) + (max(ys) - min(ys))
            return total

        def gradient(c, net_cells):
            # Gradient of squared wirelength approx
            grad_x, grad_y = 0.0, 0.0
            for net in chip["nets"]:
                if c not in net["components"]:
                    continue
                cells = [cc for cc in net["components"] if cc in pos]
                if len(cells) < 2:
                    continue
                xs = [pos[cc][0] for cc in cells]
                ys = [pos[cc][1] for cc in cells]
                cx, cy = pos[c]
                # Attractive force to net centroid
                mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
                grad_x += (mx - cx) * 0.1
                grad_y += (my - cy) * 0.1
            return grad_x, grad_y

        for step in range(iters):
            # Apply gradient to all cells
            for c in cell_names:
                gx, gy = gradient(c, None)
                pos[c][0] = max(0, min(1, pos[c][0] + self.lr * gx))
                pos[c][1] = max(0, min(1, pos[c][1] + self.lr * gy))
            self.lr *= 0.9995

        # Convert to die coordinates
        components = {}
        for c in cell_names:
            components[c] = {
                "x": pos[c][0] * die_w + die["x1"],
                "y": pos[c][1] * die_h + die["y1"],
            }

        new_chip = copy.deepcopy(chip)
        new_chip["components"] = components
        hpwl = self._compute_hpwl(new_chip)

        return {
            "algorithm": self.name,
            "components": components,
            "hpwl": hpwl,
            "time": time.time() - t0,
        }
