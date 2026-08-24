"""
Base placer class — all algorithms inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Dict
import time


class BasePlacer(ABC):
    """Base class for placement algorithms."""

    name: str = "Base"

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def place(self, chip: dict, iterations: int = None) -> dict:
        """
        Run the placement algorithm on the chip.
        Returns: {components: {cell: {x, y}}, hpwl: float, time: float}
        """
        pass

    def _compute_hpwl(self, chip: dict) -> float:
        from ..core.hpwl import compute_hpwl
        return compute_hpwl(chip)["total_hpwl"]

    def _make_random_chip(self, chip: dict, seed: int = None) -> dict:
        import random
        import copy
        if seed is not None:
            random.seed(seed)
        new_chip = copy.deepcopy(chip)
        for c in new_chip["components"]:
            new_chip["components"][c] = {
                "x": random.randint(chip["die"]["x1"], chip["die"]["x2"]),
                "y": random.randint(chip["die"]["y1"], chip["die"]["y2"]),
            }
        return new_chip
