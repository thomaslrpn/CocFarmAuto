# Changelog

Toutes les évolutions notables de CoC AutoFarm. Format inspiré de « Keep a Changelog »,
versions selon Semantic Versioning (1.0.0 = première version stable).

## 0.1.1 — 2026-11-05

### Distribution
- Première mise à jour distribuée automatiquement : sert de test bout à bout du système de mises à jour.
- Outils de publication : affichage des fichiers compilés dans le bon ordre.

## 0.1.0 — 2026-11-05

### Application de bureau (phase 7)
- Logiciel Windows autonome : installateur en français, raccourcis bureau et menu Démarrer, désinstalleur.
- Le moteur d'analyse est embarqué : démarré automatiquement avec l'application, arrêté à la fermeture.
- Une seule instance à la fois ; taille et position de la fenêtre mémorisées.
- Mises à jour automatiques signées (vérification au démarrage et toutes les 6 h, bouton dans À propos),
  avec sauvegarde de la base avant chaque installation.

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
- Installateur non signé pour Windows (avertissement SmartScreen à la première installation).
- Icône provisoire.
