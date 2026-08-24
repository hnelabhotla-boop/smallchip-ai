"""
Genetic Algorithm placer.
Population-based, with mutations and crossover.
"""

import random
import time
import copy
from .base import BasePlacer


class GeneticAlgorithm(BasePlacer):
    name = "Genetic Algorithm"

    def __init__(self, population_size: int = 20, generations: int = 50,
                 mutation_rate: float = 0.1, seed: int = 42, **kwargs):
        super().__init__(**kwargs)
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.seed = seed

    def _random_chromosome(self, chip):
        return self._make_random_chip(chip, seed=random.randint(0, 1_000_000))

    def _fitness(self, chip):
        return self._compute_hpwl(chip)

    def _mutate(self, chip, max_step=2000):
        new_chip = copy.deepcopy(chip)
        c = random.choice(list(new_chip["components"].keys()))
        pos = new_chip["components"][c]
        new_chip["components"][c] = {
            "x": max(chip["die"]["x1"], min(chip["die"]["x2"],
                                            pos["x"] + random.randint(-max_step, max_step))),
            "y": max(chip["die"]["y1"], min(chip["die"]["y2"],
                                            pos["y"] + random.randint(-max_step, max_step))),
        }
        return new_chip

    def _crossover(self, parent1, parent2):
        # Blend crossover: take x from one, y from another
        child = copy.deepcopy(parent1)
        for c in child["components"]:
            if random.random() < 0.5 and c in parent2["components"]:
                child["components"][c]["x"] = parent2["components"][c]["x"]
            if random.random() < 0.5 and c in parent2["components"]:
                child["components"][c]["y"] = parent2["components"][c]["y"]
        return child

    def place(self, chip: dict, iterations: int = None) -> dict:
        t0 = time.time()
        random.seed(self.seed)

        # Initialize population
        population = [self._random_chromosome(chip) for _ in range(self.population_size)]
        best = min(population, key=self._fitness)
        best_hpwl = self._fitness(best)

        n_gens = iterations or self.generations
        for gen in range(n_gens):
            # Tournament selection
            new_population = []
            for _ in range(self.population_size):
                t1, t2 = random.sample(population, 2)
                winner = t1 if self._fitness(t1) < self._fitness(t2) else t2
                new_population.append(copy.deepcopy(winner))

            # Crossover
            for i in range(0, len(new_population) - 1, 2):
                if random.random() < 0.5:
                    child = self._crossover(new_population[i], new_population[i + 1])
                    new_population[i] = child

            # Mutation
            for i in range(len(new_population)):
                if random.random() < self.mutation_rate:
                    new_population[i] = self._mutate(new_population[i])

            population = new_population
            gen_best = min(population, key=self._fitness)
            gen_hpwl = self._fitness(gen_best)
            if gen_hpwl < best_hpwl:
                best_hpwl = gen_hpwl
                best = copy.deepcopy(gen_best)

        return {
            "algorithm": self.name,
            "components": best["components"],
            "hpwl": best_hpwl,
            "time": time.time() - t0,
        }
