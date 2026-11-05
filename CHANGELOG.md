# Changelog

Toutes les évolutions notables de CoC AutoFarm. Format inspiré de « Keep a Changelog »,
versions selon Semantic Versioning (1.0.0 = première version stable).

## 1.0.0 — 2026-11-05

Première version stable.

### Pendant le jeu
- Mini-fenêtre toujours au-dessus du jeu : score, butin et recommandation du dernier village, démarrage
  et arrêt de l'observation. Position et taille mémorisées.
- Alerte sonore quand un bon village apparaît (carillon propre à l'application), même avec l'application
  cachée derrière le jeu. Seuil réglable (très intéressant, ou intéressant et mieux), notification
  Windows en option, bouton « Tester l'alerte ».
- Récapitulatif de fin d'attaque : butin récupéré sur butin disponible, par ressource, avec une note
  du farm sur 100 (excellent, bon, moyen, faible), dans la mini-fenêtre et dans la fiche du village.
- Ressource prioritaire et butin visé modifiables directement dans la mini-fenêtre ; le village
  affiché est recalculé aussitôt.

### Score
- La ressource prioritaire compte désormais pour 80 % de la note (au lieu de 60 %) : un village riche
  en or et en élixir mais pauvre en élixir noir n'est plus « très intéressant » quand l'élixir noir est
  prioritaire. Le mode équilibré ne change pas.

## 0.3.0 — 2026-11-05

### Reconnaissance
- Lecture fiable pour toutes les tailles de fenêtre du jeu de 960 x 540 à 2560 x 1440 (16:9).
- Avertissement dans les Logs si la fenêtre du jeu est trop petite pour une lecture fiable.

### Interface
- Nouvelle icône et nouveau logo ; installateur personnalisé (images, contrat de licence).
- Menu latéral fixe : il reste visible (avec l'encadré de mise à jour) pendant le défilement des pages.
- Plus de flash blanc à l'ouverture de la fenêtre.

### Projet
- Licence GNU AGPL v3, affichée dans À propos et dans l'installateur.
- Nouveau guide d'utilisation (README) ; la documentation technique est dans docs/DEVELOPPEMENT.md.

## 0.2.1-beta.2 — 2026-11-05

### Mises à jour
- Retour possible d'une bêta vers la dernière version stable (canal stable choisi dans les Paramètres).
- Vérification de compatibilité : le retour est bloqué si la bêta a fait évoluer la structure de la base de données.

## 0.2.1-beta.1 — 2026-11-05

### Mises à jour
- Une mise à jour bêta est clairement signalée avant son installation.
- Première version bêta : sert à tester le canal bêta (invisible pour le canal stable).

## 0.2.0 — 2026-11-05

### Mises à jour
- Canal de mises à jour au choix dans les Paramètres : stable (recommandé) ou bêta (versions de test).
- Recherche automatique des mises à jour activable ou désactivable.
- Historique des versions publiées dans la page À propos, avec leurs notes.

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
