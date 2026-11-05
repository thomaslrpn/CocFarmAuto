# Changelog

Toutes les évolutions notables de CoC AutoFarm. Format inspiré de « Keep a Changelog »,
versions selon Semantic Versioning (1.0.0 = première version stable).

## 0.1.0 — en développement

### Interface (phase 6)
- Dashboard : chiffres clés, état du moteur, démarrage / arrêt de l'observation, scores récents.
- Pages Analyse (fiche village, détail du score) et Historique (filtres, tri, miniatures).
- Pages Statistiques (évolution, répartition, comparaison des stratégies), Paramètres, Logs et À propos.

### Moteur (phases 1 à 5)
- Capture de la fenêtre du jeu, même recouverte par une autre fenêtre.
- Lecture du butin et des ressources du joueur, reconnaissance de l'écran (village, recherche, combat).
- Mode observation : enregistrement automatique de chaque village rencontré (lecture seule).
- Score de rentabilité sur 100, expliqué et personnalisable ; rang relatif par rapport aux villages vus.
- Simulation théorique et comparaison de stratégies de farm.
- Base SQLite locale avec migrations et sauvegardes automatiques.
- API locale sécurisée (jeton), logs structurés.

### Limites connues
- Détection des bâtiments (hôtel de ville, réserves, défenses) pas encore disponible.
- Une seule taille de fenêtre testée (1323 x 744).
- Pas encore d'installateur ni de mises à jour automatiques (phases 7 et 8).
