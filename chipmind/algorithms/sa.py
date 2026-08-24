"""
Simulated Annealing — fast, in-place implementation.
Each move modifies one cell in-place; no expensive deepcopy per iteration.
"""

import math
import random
import time
from .base import BasePlacer


class SimulatedAnnealing(BasePlacer):
    """Multi-stage simulated annealing with in-place moves."""

    name = "Simulated Annealing"

    def __init__(self, iterations_per_stage: int = 20000, num_stages: int = 10,
                 initial_temp: float = 30000, cooling_rate: float = 0.999,
                 max_step: int = 2000, seed: int = 42, **kwargs):
        super().__init__(**kwargs)
        self.iterations_per_stage = iterations_per_stage
        self.num_stages = num_stages
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.max_step = max_step
        self.seed = seed

    def place(self, chip: dict, iterations: int = None) -> dict:
        t0 = time.time()
        random.seed(self.seed)

        # Initialize with random positions
        die = chip["die"]
        comp_names = list(chip["components"].keys())
        for c in comp_names:
            chip["components"][c] = {
                "x": random.randint(die["x1"], die["x2"]),
                "y": random.randint(die["y1"], die["y2"]),
            }

        # Build net index for fast HPWL: cell -> set of nets it belongs to
        cell_nets = {c: [] for c in comp_names}
        for i, net in enumerate(chip["nets"]):
            for c in net["components"]:
                if c in cell_nets:
                    cell_nets[c].append(i)

        def fast_hpwl():
            total = 0
            for net in chip["nets"]:
                cells = [c for c in net["components"] if c in chip["components"]]
                if len(cells) < 2:
                    continue
                xs = [chip["components"][c]["x"] for c in cells]
                ys = [chip["components"][c]["y"] for c in cells]
                total += (max(xs) - min(xs)) + (max(ys) - min(ys))
            return total

        current_hpwl = fast_hpwl()
        best_chip = {c: dict(chip["components"][c]) for c in comp_names}
        best_hpwl = current_hpwl

        if iterations is not None:
            stages = [(iterations, self.initial_temp, self.cooling_rate, self.max_step)]
        else:
            base_stages = [
                (20000, 30000, 0.999, 2000),
                (20000, 15000, 0.999, 1000),
                (20000, 8000, 0.999, 500),
                (20000, 4000, 0.999, 300),
                (20000, 2000, 0.999, 150),
                (20000, 1000, 0.999, 100),
                (20000, 500, 0.999, 75),
                (20000, 200, 0.999, 50),
                (20000, 100, 0.9995, 30),
                (20000, 50, 0.9995, 15),
            ]
            stages = [(self.iterations_per_stage, t, c, s) for (it, t, c, s) in base_stages[:self.num_stages]]

        for stage_idx, (iters, temp, cool, step) in enumerate(stages):
            T = temp
            for i in range(iters):
                c = random.choice(comp_names)
                pos = chip["components"][c]
                old_x, old_y = pos["x"], pos["y"]
                new_x = max(die["x1"], min(die["x2"], old_x + random.randint(-step, step)))
                new_y = max(die["y1"], min(die["y2"], old_y + random.randint(-step, step)))
                pos["x"], pos["y"] = new_x, new_y
                new_hpwl = fast_hpwl()
                delta = new_hpwl - current_hpwl
                if delta < 0 or random.random() < math.exp(-delta / max(T, 1)):
                    current_hpwl = new_hpwl
                else:
                    pos["x"], pos["y"] = old_x, old_y
                if current_hpwl < best_hpwl:
                    best_hpwl = current_hpwl
                    for cn in comp_names:
                        best_chip[cn] = dict(chip["components"][cn])
                T *= cool

        return {
            "algorithm": self.name,
            "components": best_chip,
            "hpwl": best_hpwl,
            "time": time.time() - t0,
        }
