# CAHIER DES CHARGES COMPLET — CoC AutoFarm

## 1. Présentation générale du projet

Je souhaite développer un logiciel personnel nommé **CoC AutoFarm**.

Il s'agit d'un assistant intelligent dédié à l'analyse et à l'optimisation du farm sur Clash of Clans.

Le jeu sera exécuté sur PC Windows via Google Play Games.

L'objectif est de développer un véritable logiciel de bureau, moderne, performant, modulaire et distribuable à d'autres utilisateurs.

Je ne souhaite pas simplement créer un script Python ou une application web locale. Je veux développer un produit logiciel complet, avec :
- Une interface graphique professionnelle.
- Un moteur d'analyse visuelle.
- Un système intelligent d'évaluation des villages.
- Un moteur de décision et de simulation stratégique.
- Une base de données locale.
- Un système de statistiques.
- Un installateur Windows.
- Un système de mises à jour automatiques.
- Une infrastructure permettant de distribuer les nouvelles versions à tous les utilisateurs.

Le projet doit être conçu dès le départ pour pouvoir évoluer et accueillir de nouvelles fonctionnalités.

**Important :** le logiciel doit rester un outil d'analyse, d'aide à la décision et de simulation. Il ne doit pas contourner les protections du jeu ni automatiser les combats réels.

---

# 2. Objectif fonctionnel

Je souhaite que le logiciel soit capable d'observer Clash of Clans et d'analyser automatiquement les villages rencontrés.

Le fonctionnement souhaité est le suivant :

1. Le logiciel observe l'écran de Google Play Games.
2. Il détecte l'état actuel du jeu.
3. Il identifie les ressources visibles.
4. Il analyse les caractéristiques du village adverse.
5. Il estime le butin potentiellement récupérable.
6. Il calcule un score de rentabilité.
7. Il détermine si le village est intéressant.
8. Il recommande une stratégie de farm.
9. Il simule les résultats théoriques de différentes stratégies.
10. Il enregistre les résultats.
11. Il affiche les informations dans son dashboard.

L'utilisateur doit pouvoir comprendre les décisions du moteur et consulter les résultats de chaque analyse.

---

# 3. Environnement technique

## Système d'exploitation

- Windows 10.
- Windows 11.
- Jeu exécuté avec Google Play Games pour PC.

## Backend

Langage principal : Python.

Technologies envisagées :
- Python 3.11 ou version compatible.
- FastAPI pour l'API locale.
- OpenCV pour le traitement d'images.
- NumPy pour les calculs.
- Pillow pour la manipulation des images.
- MSS pour les captures d'écran.
- Pydantic pour la validation des données.
- SQLite pour la base de données.
- SQLAlchemy pour l'accès aux données.
- Pytest pour les tests.

## Frontend

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- Recharts pour les graphiques.
- Lucide pour les icônes.

## Application de bureau

Étudier les solutions :
- Tauri.
- Electron.

Je souhaite privilégier Tauri si son intégration avec Python est adaptée au projet.

L'objectif est de produire une application Windows autonome et distribuable.

---

# 4. Architecture générale

Je souhaite séparer clairement les différentes responsabilités.

### Capture
Récupération des images du jeu.

### Vision
Reconnaissance des éléments visuels.

### Analysis
Analyse des villages et calcul de rentabilité.

### Strategy
Simulation et comparaison des stratégies de farm.

### Database
Stockage local des données.

### API
Communication entre le backend et le frontend.

### Frontend
Interface graphique de gestion et de visualisation.

### Desktop
Application Windows, packaging et mises à jour.

Chaque module doit être indépendant et testable.

---

# 5. Module de capture d'écran

Créer un module `capture/`.

Responsabilités :
- Capturer l'écran de Google Play Games.
- Pouvoir cibler la fenêtre du jeu.
- Détecter si la fenêtre est disponible.
- Gérer différentes résolutions.
- Enregistrer les captures.
- Horodater les images.
- Permettre une prévisualisation.
- Gérer les erreurs de capture.

Je souhaite éviter de capturer l'intégralité du bureau lorsque seule la fenêtre du jeu est nécessaire.

Les captures seront enregistrées dans un dossier dédié.

---

# 6. Module de reconnaissance visuelle

Créer un module `vision/`.

L'objectif est de permettre au logiciel de comprendre les éléments visibles dans Clash of Clans.

Éléments à reconnaître :

### Ressources
- Or.
- Élixir.
- Élixir noir.

### Bâtiments
- Réserves d'or.
- Réserves d'élixir.
- Réserves d'élixir noir.
- Mines d'or.
- Extracteurs d'élixir.
- Foreuses d'élixir noir.
- Hôtel de ville.
- Défenses principales.

### Informations complémentaires
- Quantités de ressources affichées.
- Niveau apparent des bâtiments.
- Position des bâtiments.
- Répartition des ressources.
- État de l'interface.

Technologies envisagées :

**OpenCV :**
- Détection par template matching.
- Reconnaissance de zones.
- Analyse des couleurs.
- Traitement d'images.

**YOLO :**
À envisager si une détection par modèle devient nécessaire.

Chaque détection doit contenir :
- Type d'élément.
- Position X/Y.
- Dimensions.
- Niveau de confiance.
- Valeur reconnue si applicable.

Prévoir un système de correction manuelle des détections.

---

# 7. Module d'analyse des villages

Créer `analysis/village.py`.

Ce module devra analyser les informations récupérées par la reconnaissance visuelle.

Informations à produire :

- Quantité d'or disponible.
- Quantité d'élixir disponible.
- Quantité d'élixir noir disponible.
- Répartition des ressources.
- Position des réserves.
- Position des extracteurs.
- Accessibilité théorique des ressources.
- Protection apparente des ressources.
- Niveau de difficulté estimé.

Chaque village doit générer une fiche d'analyse complète.

---

# 8. Algorithme de rentabilité

Créer `analysis/profitability.py`.

Je souhaite développer un algorithme capable de déterminer si un village présente un bon potentiel de farm.

Le calcul doit prendre en compte :

- Or disponible.
- Élixir disponible.
- Élixir noir disponible.
- Coût théorique des troupes.
- Difficulté estimée.
- Temps théorique.
- Risque de perte de trophées.
- Rendement estimé.

Le moteur doit attribuer un score compréhensible.

Exemple de résultat :

Village A :
- Or : 650 000.
- Élixir : 720 000.
- Élixir noir : 5 000.
- Difficulté : moyenne.
- Rentabilité : 87/100.
- Recommandation : très intéressant.

Les chiffres ci-dessus sont uniquement des exemples de données de test.

Prévoir des paramètres personnalisables :
- Ressource prioritaire.
- Quantité minimale de butin.
- Difficulté maximale.
- Importance de l'élixir noir.
- Importance du temps.
- Importance du rendement.

Le score doit être expliqué à l'utilisateur.

---

# 9. Module de stratégie et simulation

Créer un module `strategy/`.

Il doit permettre de comparer différentes stratégies théoriques.

Exemples :

- Farm orienté or.
- Farm orienté élixir.
- Farm orienté élixir noir.
- Farm équilibré.

Le moteur doit simuler :
- Coût théorique des troupes.
- Butin estimé.
- Temps théorique.
- Rendement.
- Difficulté.
- Résultat potentiel.

Les stratégies doivent pouvoir être comparées dans le dashboard.

Le système doit rester indépendant du jeu réel.

---

# 10. Base de données locale

Utiliser SQLite.

La base de données devra contenir plusieurs tables.

### Table Villages
- id
- date_analyse
- quantite_or
- quantite_elixir
- quantite_elixir_noir
- score_rentabilite
- difficulte_estimee
- strategie_recommandee

### Table Analyses
- id
- village_id
- date_analyse
- resultat
- confiance_detection

### Table Statistiques
- id
- date
- nombre_villages
- ressources_analysees
- score_moyen

### Table Paramètres
- id
- nom
- valeur

Prévoir une architecture évolutive.

Chaque utilisateur doit disposer de sa propre base de données locale.

---

# 11. Interface graphique — Dashboard

Je souhaite une interface moderne, sombre, élégante et professionnelle.

L'identité visuelle doit être cohérente sur toutes les pages.

## Page Dashboard

Afficher :
- Nombre de villages analysés.
- Total des ressources identifiées.
- Score moyen de rentabilité.
- Historique récent.
- Graphiques de progression.
- État du moteur d'analyse.

## Page Analyse

Afficher :
- Capture actuelle.
- Village analysé.
- Ressources détectées.
- Zones reconnues.
- Score de rentabilité.
- Détail du calcul.
- Stratégie recommandée.

## Page Historique

Afficher :
- Tous les villages analysés.
- Date et heure.
- Ressources.
- Rentabilité.
- Difficulté estimée.
- Capture associée.

Prévoir une recherche et des filtres.

## Page Statistiques

Afficher :
- Évolution du rendement.
- Quantités de ressources analysées.
- Rentabilité moyenne.
- Répartition des ressources.
- Comparaison des stratégies.

## Page Paramètres

Permettre de configurer :
- Ressource prioritaire.
- Seuil de rentabilité.
- Paramètres de reconnaissance.
- Résolution de capture.
- Fréquence des analyses.
- Préférences de l'application.

## Page Logs

Afficher :
- Captures effectuées.
- Analyses terminées.
- Détections.
- Erreurs.
- Temps d'exécution.
- État des modules.

## Page À propos

Afficher :
- Version actuelle.
- Informations du logiciel.
- Changelog.
- Recherche de mises à jour.
- Informations de licence éventuelles.

---

# 12. Structure du projet

Proposer une organisation similaire à celle-ci :

CoC-AutoFarm/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── capture/
│   │   │   ├── screen.py
│   │   │   └── window.py
│   │   ├── vision/
│   │   │   ├── resources.py
│   │   │   ├── buildings.py
│   │   │   ├── detector.py
│   │   │   └── village.py
│   │   ├── analysis/
│   │   │   ├── profitability.py
│   │   │   ├── scoring.py
│   │   │   └── village_analysis.py
│   │   ├── strategy/
│   │   │   ├── simulator.py
│   │   │   └── strategies.py
│   │   ├── database/
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   └── api/
│   │       └── routes.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── App.tsx
│   └── package.json
│
├── desktop/
│   ├── src-tauri/
│   └── updater/
│
├── screenshots/
├── datasets/
├── tests/
├── releases/
└── README.md

Cette structure peut être adaptée si une meilleure architecture est identifiée.

---

# 13. TRÈS IMPORTANT : Application Windows distribuable

Je ne veux pas que CoC AutoFarm reste un projet qui nécessite de lancer manuellement Python, npm ou un serveur local.

Je souhaite créer un véritable logiciel Windows.

L'utilisateur final doit pouvoir télécharger un installateur, installer le programme et l'utiliser directement.

## 13.1 Installation

Créer un installateur Windows permettant :

- D'installer le logiciel.
- De créer un raccourci sur le bureau.
- D'ajouter le programme au menu Démarrer.
- De gérer les fichiers nécessaires.
- D'installer les composants embarqués.
- De désinstaller proprement le programme.

L'utilisateur ne doit pas avoir besoin d'installer Python ou Node.js.

## 13.2 Packaging

Étudier les technologies suivantes :

- Tauri pour l'application de bureau.
- Electron comme alternative.
- PyInstaller ou Nuitka pour embarquer Python.
- Inno Setup ou NSIS pour produire l'installateur Windows.

Je privilégie une solution légère, fiable et facile à maintenir.

Le backend Python devra être embarqué dans l'application.

Le frontend React devra être compilé et intégré à l'application.

L'ensemble devra fonctionner sans serveur de développement.

## 13.3 Mises à jour automatiques

Je souhaite intégrer un système de mises à jour automatiques.

Fonctionnement attendu :

1. L'application vérifie si une nouvelle version est disponible.
2. Elle compare la version installée avec la dernière version publiée.
3. Elle informe l'utilisateur.
4. Elle télécharge la mise à jour.
5. Elle vérifie l'intégrité du fichier.
6. Elle installe la nouvelle version.
7. Elle redémarre si nécessaire.

Prévoir :
- Un bouton « Rechercher des mises à jour ».
- Une vérification automatique périodique.
- Un indicateur de progression.
- Un historique des versions.
- Un changelog.
- Une gestion des erreurs.
- Une procédure de récupération en cas d'échec.

Les mises à jour devront être sécurisées avec signatures et/ou vérification cryptographique.

## 13.4 Distribution centralisée

Je souhaite pouvoir publier les nouvelles versions du logiciel et les distribuer à tous les utilisateurs.

Étudier GitHub Releases comme solution de départ.

Prévoir :
- Un dépôt centralisé.
- Des versions numérotées.
- Des installateurs téléchargeables.
- Des fichiers de métadonnées.
- Des notes de version.
- Un système de publication.
- Une vérification de compatibilité.

Mon objectif est simple :

Je développe une nouvelle version sur mon ordinateur, je la compile, je la publie et tous les utilisateurs ayant téléchargé CoC AutoFarm peuvent recevoir la mise à jour directement depuis leur application.

Je ne veux pas devoir contacter chaque utilisateur individuellement.

## 13.5 Gestion des versions

Adopter Semantic Versioning :

- 1.0.0 : version initiale.
- 1.0.1 : correctif.
- 1.1.0 : nouvelle fonctionnalité.
- 2.0.0 : évolution majeure.

Prévoir trois canaux :
- Développement.
- Bêta.
- Stable.

Les utilisateurs doivent pouvoir rester sur le canal stable.

## 13.6 Gestion des données utilisateurs

Chaque installation doit posséder ses propres données :

- Configuration.
- Base SQLite.
- Historique.
- Captures.
- Préférences.

Les mises à jour du logiciel ne doivent jamais écraser ces données.

Prévoir des sauvegardes et des migrations de base de données.

Le fonctionnement principal doit rester local afin de limiter les coûts d'infrastructure.

## 13.7 Identité du logiciel

Je souhaite une identité visuelle professionnelle :

- Nom : CoC AutoFarm.
- Icône personnalisée.
- Installateur personnalisé.
- Écran de démarrage.
- Fenêtre de mise à jour.
- Informations de version.
- Page À propos.

L'application doit donner l'impression d'un logiciel fini et non d'un simple outil de développeur.

---

# 14. Sécurité et fiabilité

Le logiciel doit être robuste.

Prévoir :
- Gestion centralisée des erreurs.
- Logs structurés.
- Validation des entrées.
- Séparation des données utilisateur et des fichiers applicatifs.
- Sauvegardes SQLite.
- Vérification des mises à jour.
- Protection contre les fichiers corrompus.
- Tests automatisés.
- Gestion des processus backend.
- Arrêt propre de l'application.

Ne jamais intégrer de secrets ou de clés privées dans le frontend ou l'exécutable.

---

# 15. Tests

Utiliser Pytest pour le backend.

Prévoir des tests pour :
- Les captures d'écran.
- Les fonctions de reconnaissance.
- Le calcul des ressources.
- L'algorithme de rentabilité.
- Les simulations.
- Les accès à la base de données.
- Les API.

Prévoir également des tests frontend.

Les mises à jour devront être testées sur une version bêta avant leur publication stable.

---

# 16. Qualité du code et méthode de développement

Je suis développeur web et je connais notamment :
- JavaScript.
- TypeScript.
- React.
- Les bases de Python.

Je souhaite comprendre le fonctionnement du projet et progresser techniquement.

Respecter impérativement les règles suivantes :

- Code propre et modulaire.
- Fonctions et classes bien organisées.
- Commentaires utiles.
- Typage lorsque pertinent.
- Gestion des exceptions.
- Logs.
- Tests unitaires.
- Pas de code inutilement complexe.
- Pas de duplication.
- Pas de fichiers gigantesques.
- Architecture maintenable.

Ne jamais prétendre qu'une fonctionnalité est terminée si elle n'a pas été testée.

Ne pas remplacer une fonctionnalité réelle par une simulation sans le préciser.

---

# 17. Méthode de travail obligatoire

Je ne souhaite pas que tu génères l'intégralité du projet dans une seule réponse.

Nous allons développer CoC AutoFarm progressivement.

Pour chaque étape :

1. Explique l'objectif.
2. Présente les technologies utilisées.
3. Indique les fichiers à créer ou modifier.
4. Donne le code complet.
5. Explique les parties importantes.
6. Donne les commandes PowerShell.
7. Explique comment lancer et tester.
8. Attends mon retour avant de passer à la suite.

Si une erreur apparaît, corrigeons-la avant de continuer.

Ne modifie pas inutilement des fichiers qui ne concernent pas l'étape actuelle.

Conserve une cohérence entre toutes les étapes et rappelle les décisions architecturales déjà prises.

---

# 18. Feuille de route du développement

Je souhaite suivre cet ordre :

### Phase 1 — Initialisation
- Vérification de l'environnement Windows.
- Création du dépôt Git.
- Création de l'arborescence.
- Installation Python.
- Configuration du backend.
- Première capture d'écran.

### Phase 2 — Reconnaissance visuelle
- Détection de la fenêtre Google Play Games.
- Traitement des images.
- Reconnaissance des ressources.
- Détection des bâtiments.
- Tests sur captures réelles.

### Phase 3 — Analyse
- Construction des fiches villages.
- Extraction des ressources.
- Calcul du butin estimé.
- Calcul du score de rentabilité.

### Phase 4 — Stratégies
- Création des stratégies théoriques.
- Simulation.
- Comparaison des rendements.

### Phase 5 — Backend
- API FastAPI.
- SQLite.
- Historique.
- Gestion des paramètres.

### Phase 6 — Frontend
- Création du dashboard.
- Pages d'analyse.
- Historique.
- Statistiques.
- Paramètres.
- Logs.

### Phase 7 — Application de bureau
- Intégration Tauri.
- Intégration du backend Python.
- Gestion des processus.
- Packaging.

### Phase 8 — Distribution
- Création de l'installateur Windows.
- Configuration de GitHub Releases.
- Système de mises à jour.
- Gestion des versions.
- Tests sur plusieurs machines.

### Phase 9 — Version 1.0
- Tests complets.
- Correction des bugs.
- Optimisation.
- Documentation.
- Création de la première version stable.

---

# 19. Première demande à Claude

Commence par étudier intégralement ce cahier des charges.

Je veux que tu me proposes :

1. Une architecture technique définitive et cohérente.
2. Une comparaison entre Tauri et Electron pour ce projet.
3. La meilleure façon d'intégrer et d'embarquer Python.
4. La meilleure solution pour les mises à jour automatiques.
5. Une arborescence de projet définitive.
6. Une feuille de route réaliste.

Ne commence pas à développer toutes les fonctionnalités immédiatement.

Commence uniquement par la préparation de l'environnement et la première capture d'écran fonctionnelle.

**Je veux construire un véritable logiciel Windows distribuable, et pas simplement un script qui fonctionne sur mon ordinateur.**

Le système de distribution et de mise à jour doit être pensé dès le départ, même si son implémentation intervient plus tard.