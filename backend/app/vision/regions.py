"""Zones d'intérêt de l'écran, exprimées en PROPORTIONS de la capture.

Pourquoi des proportions ? Pour qu'une même définition fonctionne quelle que
soit la taille de la fenêtre (1323x744, 1920x1080...). Une zone (0.5, 0.5, 1, 1)
désigne toujours le quart inférieur droit.

Limite : l'interface de CoC reste ancrée aux bords de l'écran. Si le RAPPORT
largeur/hauteur change beaucoup (ex. 4:3 au lieu de 16:9), les zones peuvent
dériver ; on ajoutera alors un ancrage par bord si nécessaire.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.vision.models import Box, ElementType


@dataclass(frozen=True)
class RelativeRegion:
    """Rectangle défini par des fractions (0.0 à 1.0) de la largeur / hauteur."""

    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.left < self.right <= 1.0 and 0.0 <= self.top < self.bottom <= 1.0):
            raise ValueError(f"Région relative invalide : {self}")

    @classmethod
    def from_pixels(cls, x0: int, y0: int, x1: int, y1: int, ref_width: int, ref_height: int) -> "RelativeRegion":
        """Crée une région à partir de pixels mesurés sur une capture de référence."""
        return cls(x0 / ref_width, y0 / ref_height, x1 / ref_width, y1 / ref_height)

    def to_box(self, image_width: int, image_height: int) -> Box:
        """Convertit en pixels pour une image de la taille donnée."""
        x0, y0 = round(self.left * image_width), round(self.top * image_height)
        x1, y1 = round(self.right * image_width), round(self.bottom * image_height)
        return Box(x0, y0, max(1, x1 - x0), max(1, y1 - y0))


# Hauteur de fenêtre des captures de référence (1323x744) : toutes les mesures en
# pixels du module vision (seuils de découpe, modèles) correspondent à cette taille.
REFERENCE_HEIGHT = 744
# En dessous, les chiffres font moins de 10 pixels : lecture non garantie
# (mesuré : lecture exacte de 960x540 à 2560x1440, voir tests/test_resolutions.py).
MIN_SUPPORTED_HEIGHT = 540

# Compteurs de ressources du VILLAGE DU JOUEUR (en haut à droite).
# Mesurés sur une capture réelle 1323x744 (16:9) : texte haut d'environ 13 px.
HOME_RESOURCE_REGIONS: dict[ElementType, RelativeRegion] = {
    ElementType.GOLD: RelativeRegion(0.8466, 0.0242, 0.9637, 0.0618),
    ElementType.ELIXIR: RelativeRegion(0.8466, 0.0820, 0.9637, 0.1196),
    ElementType.DARK_ELIXIR: RelativeRegion(0.8466, 0.1384, 0.9637, 0.1761),
}

# « Butin disponible » sur l'écran de RECHERCHE D'ADVERSAIRE (en haut à gauche).
# Mesuré sur 4 captures réelles 1323x744 ; la ligne « Butin disponible : » est exclue.
LOOT_RESOURCE_REGIONS: dict[ElementType, RelativeRegion] = {
    ElementType.GOLD: RelativeRegion(0.0393, 0.1022, 0.1323, 0.1358),
    ElementType.ELIXIR: RelativeRegion(0.0393, 0.1452, 0.1323, 0.1788),
    ElementType.DARK_ELIXIR: RelativeRegion(0.0393, 0.1895, 0.1323, 0.2231),
}

# Jeux de zones par nom (utilisés par les outils et le fichier d'annotations).
REGION_SETS: dict[str, dict[ElementType, RelativeRegion]] = {
    "home": HOME_RESOURCE_REGIONS,
    "loot": LOOT_RESOURCE_REGIONS,
}
