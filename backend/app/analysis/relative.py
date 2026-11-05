"""Score RELATIF : comment un village se situe par rapport à ceux déjà vus.

Le score sur 100 est plafonné (un village au-delà du butin visé a 100). Le rang
relatif utilise la valeur NON plafonnée du butin et répond à la question :
« ce village est-il meilleur que la plupart de ceux que j'ai rencontrés ? »
"""
from __future__ import annotations

from bisect import bisect_left
from collections.abc import Sequence


class RelativeRanker:
    """Calcule des rangs en pourcentage à partir d'une population de valeurs."""

    def __init__(self, population: Sequence[float]) -> None:
        self._sorted = sorted(population)

    def percentile(self, value: float) -> float | None:
        """% des AUTRES villages de la population ayant une valeur strictement inférieure.

        Ex. 85.0 = « meilleur que 85 % des villages vus ». None si la population
        ne contient pas d'autre village (aucune comparaison possible).
        """
        others = len(self._sorted) - 1  # la population contient le village lui-même
        if others <= 0:
            return None
        below = bisect_left(self._sorted, value)
        return round(100 * below / others, 1)
