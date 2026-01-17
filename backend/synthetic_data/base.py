"""Base generator class for synthetic data generation.

Provides common functionality for all generators including:
- Deterministic random number generation via seed
- Validation interface
- Generation interface
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any


class BaseGenerator(ABC):
    """Base class for synthetic data generators.

    Provides:
    - Seeded random number generation for reproducibility
    - Abstract generate() and validate() methods
    - Utility methods for random selection

    Usage:
        class MyGenerator(BaseGenerator):
            def generate(self, count: int) -> list[dict]:
                return [self._generate_item() for _ in range(count)]

            def validate(self, item: dict) -> bool:
                return "required_field" in item
    """

    def __init__(self, seed: int = 42):
        """Initialize generator with seed for reproducibility.

        Args:
            seed: Random seed for deterministic generation
        """
        self.seed = seed
        self.rng = random.Random(seed)

    def reset_seed(self) -> None:
        """Reset the random number generator to initial seed."""
        self.rng = random.Random(self.seed)

    @abstractmethod
    def generate(self, count: int) -> list[dict[str, Any]]:
        """Generate synthetic data items.

        Args:
            count: Number of items to generate

        Returns:
            List of generated data dictionaries
        """
        pass

    @abstractmethod
    def validate(self, item: dict[str, Any]) -> bool:
        """Validate a generated item.

        Args:
            item: Data item to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def generate_validated(self, count: int) -> list[dict[str, Any]]:
        """Generate items and filter to only valid ones.

        Args:
            count: Target number of valid items

        Returns:
            List of validated items
        """
        items = []
        attempts = 0
        max_attempts = count * 3  # Allow some failures

        while len(items) < count and attempts < max_attempts:
            batch = self.generate(min(count - len(items), 10))
            for item in batch:
                if self.validate(item):
                    items.append(item)
                    if len(items) >= count:
                        break
            attempts += 1

        return items

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _choice(self, items: list[Any]) -> Any:
        """Randomly select one item from a list."""
        return self.rng.choice(items)

    def _choices(self, items: list[Any], k: int) -> list[Any]:
        """Randomly select k items from a list (with replacement)."""
        return self.rng.choices(items, k=k)

    def _sample(self, items: list[Any], k: int) -> list[Any]:
        """Randomly select k unique items from a list."""
        k = min(k, len(items))
        return self.rng.sample(items, k=k)

    def _shuffle(self, items: list[Any]) -> list[Any]:
        """Return a shuffled copy of the list."""
        items_copy = items.copy()
        self.rng.shuffle(items_copy)
        return items_copy

    def _uniform(self, low: float, high: float) -> float:
        """Generate a random float in [low, high)."""
        return self.rng.uniform(low, high)

    def _randint(self, low: int, high: int) -> int:
        """Generate a random integer in [low, high]."""
        return self.rng.randint(low, high)

    def _probability(self, p: float) -> bool:
        """Return True with probability p."""
        return self.rng.random() < p

    def _weighted_choice(self, items: list[Any], weights: list[float]) -> Any:
        """Select an item with given weights."""
        return self.rng.choices(items, weights=weights, k=1)[0]

    def _generate_id(self, prefix: str, length: int = 8) -> str:
        """Generate a random ID with given prefix."""
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        suffix = "".join(self.rng.choices(chars, k=length))
        return f"{prefix}_{suffix}"
