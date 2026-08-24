"""
chipmind/core/chip.py — Chip and Placement data classes
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Placement:
    """A placement is a mapping from cell names to (x, y) coordinates."""
    positions: Dict[str, Dict[str, float]]

    def items(self):
        return self.positions.items()

    def __len__(self):
        return len(self.positions)

    def __getitem__(self, name):
        return self.positions[name]

    def __setitem__(self, name, pos):
        self.positions[name] = pos

    def to_dict(self):
        return self.positions


@dataclass
class Chip:
    """A chip design: die area, cells, and netlist."""
    name: str
    die: Dict[str, int]  # {x1, y1, x2, y2}
    components: Dict[str, Dict[str, float]]  # {name: {x, y}}
    nets: List[Dict]  # [{name, components: [cell_names]}]

    @property
    def n_cells(self) -> int:
        return len(self.components)

    @property
    def n_nets(self) -> int:
        return len(self.nets)

    def cell_names(self) -> List[str]:
        return list(self.components.keys())

    def randomize(self, seed: int = None) -> "Chip":
        """Return a new Chip with random positions."""
        import random
        if seed is not None:
            random.seed(seed)
        new_components = {}
        for c in self.components:
            new_components[c] = {
                "x": random.randint(self.die["x1"], self.die["x2"]),
                "y": random.randint(self.die["y1"], self.die["y2"]),
            }
        return Chip(self.name, self.die, new_components, self.nets)

    def copy(self) -> "Chip":
        import copy
        return Chip(self.name, copy.deepcopy(self.die),
                    copy.deepcopy(self.components), copy.deepcopy(self.nets))
