# ruff: noqa: E501, S311
"""Evolutionary algorithms: train tiny neural networks, evolve weights, evaluate fitness."""
from __future__ import annotations

import random

from core.skills.registry import tool


@tool()
def train_small_nn(layers_json: str = "[2, 4, 1]", epochs: int = 100, lr: float = 0.01) -> str:
    """Train a tiny feed-forward neural network with random data using numpy."""
    try:
        import json as jsonlib

        import numpy as np
        layers = jsonlib.loads(layers_json)
        if not isinstance(layers, list) or len(layers) < 2:
            return "layers must be a JSON list with at least 2 elements [input, hidden..., output]"
        np.random.seed(42)
        weights = []
        biases = []
        for i in range(len(layers) - 1):
            w = np.random.randn(layers[i], layers[i + 1]) * 0.1
            b = np.zeros((1, layers[i + 1]))
            weights.append(w)
            biases.append(b)
        x = np.random.randn(100, layers[0])
        y = (np.sum(x, axis=1, keepdims=True) > 0).astype(float)
        losses = []
        for epoch in range(min(epochs, 1000)):
            a = x
            for w, b in zip(weights, biases):
                a = np.tanh(a @ w + b)
            loss = np.mean((a - y) ** 2)
            losses.append(loss)
            grad = 2 * (a - y) / len(x)
            for i in range(len(weights) - 1, -1, -1):
                weights[i] -= lr * (a.T @ grad if i == len(weights) - 1 else x.T @ grad)
                grad = grad @ weights[i].T * (1 - np.tanh(x @ weights[i] + biases[i]) ** 2)
        return (
            f"Trained {len(layers)}-layer NN ({layers}):\n"
            f"  Epochs: {epochs}\n"
            f"  Final loss: {losses[-1]:.6f}\n"
            f"  Initial loss: {losses[0]:.6f}\n"
            f"  Loss improvement: {(1 - losses[-1] / (losses[0] or 1e-8)) * 100:.1f}%"
        )
    except ImportError:
        return "numpy not available. Install: pip install numpy"
    except Exception as e:
        return f"NN training failed: {e}"


@tool()
def evolve_weights(population_size: int = 10, generations: int = 20) -> str:
    """Evolve a population of random weight vectors toward a target fitness using a genetic algorithm."""
    try:
        target = [random.random() for _ in range(10)]
        pop = [[random.random() for _ in range(10)] for _ in range(population_size)]
        def fitness(individual):
            return -sum((a - b) ** 2 for a, b in zip(individual, target))
        best_fitness_history = []
        for gen in range(generations):
            scored = [(fitness(ind), ind) for ind in pop]
            scored.sort(key=lambda x: x[0], reverse=True)
            best = scored[0]
            best_fitness_history.append(best[0])
            new_pop = [best[1]]
            while len(new_pop) < population_size:
                p1 = random.choice(scored[:max(2, population_size // 2)])[1]
                p2 = random.choice(scored[:max(2, population_size // 2)])[1]
                crossover = [(a + b) / 2 for a, b in zip(p1, p2)]
                mutated = [min(1.0, max(0.0, v + random.gauss(0, 0.1))) for v in crossover]
                new_pop.append(mutated)
            pop = new_pop
        return (
            f"Genetic algorithm ({generations} generations, population {population_size}):\n"
            f"  Best fitness: {best_fitness_history[-1]:.4f}\n"
            f"  Initial fitness: {best_fitness_history[0]:.4f}\n"
            f"  Improvement: {(best_fitness_history[-1] - best_fitness_history[0]) / (abs(best_fitness_history[0]) or 1e-8) * 100:.1f}%"
        )
    except Exception as e:
        return f"Evolution failed: {e}"


@tool()
def check_fitness(weights_json: str, target_json: str = "") -> str:
    """Evaluate the fitness of a weight vector against a target."""
    try:
        import json as jsonlib
        weights = jsonlib.loads(weights_json)
        if not isinstance(weights, list):
            return "weights must be a JSON array of numbers"
        if target_json:
            target = jsonlib.loads(target_json)
        else:
            target = [0.5] * len(weights)
        if len(weights) != len(target):
            return f"Weights ({len(weights)}) and target ({len(target)}) must have same length"
        mse = sum((a - b) ** 2 for a, b in zip(weights, target)) / len(weights)
        return f"Fitness evaluation:\n  MSE vs target: {mse:.6f}\n  Max deviation: {max(abs(a - b) for a, b in zip(weights, target)):.4f}"
    except Exception as e:
        return f"Fitness check failed: {e}"
