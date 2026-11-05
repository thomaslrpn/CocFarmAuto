# CoC AutoFarm

Assistant d'analyse et d'optimisation du farm pour Clash of Clans (Windows, Google Play Games).
Outil d'aide à la décision et de simulation uniquement.

Cahier des charges : [CLAUDE.md](CLAUDE.md) · Architecture : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Phase 1 — Première capture (Windows, PowerShell)

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.capture_cli          # capture la fenêtre du jeu (ou --full pour tout l'écran)
cd ..; pytest                      # tests
```

Les captures sont enregistrées dans `%LOCALAPPDATA%\CoCAutoFarm\screenshots`.

## Phase 2 — Reconnaissance visuelle (outils de développement)

```powershell
cd backend
python -m app.capture_cli            # capture (fonctionne même si la fenêtre est recouverte)
python -m app.vision_debug           # écran reconnu + ressources lues sur la dernière capture
python -m app.build_templates        # régénère les modèles après ajout de captures annotées
python -m app.observe_cli            # mode observation : enregistre chaque village rencontré (Ctrl+C pour arrêter)
```

- Images annotées : `%LOCALAPPDATA%\CoCAutoFarm\debug`.
- Villages observés : `%LOCALAPPDATA%\CoCAutoFarm\observations` (un PNG + un JSON par village).
- Captures d'entraînement : `datasets/*.png` (non versionnées) ; valeurs attendues : `datasets/labels.json` (versionné).

## Phase 3 — Rentabilité

```powershell
python -m app.analyze_cli            # classe les villages observés par score, détaille le meilleur
python -m app.analyze_cli --explain 3
```

Préférences (optionnel) : `%LOCALAPPDATA%\CoCAutoFarm\preferences.json`, par exemple :

```json
{
  "priority": "balanced",
  "target_loot": {"gold": 600000, "elixir": 600000, "dark_elixir": 10000},
  "army_cost": {"gold": 0, "elixir": 0, "dark_elixir": 0},
  "dark_elixir_importance": 1.0,
  "min_gold_elixir": 0
}
```
`priority` : `balanced`, `gold`, `elixir` ou `dark_elixir`.

## Phase 4 — Stratégies (simulation théorique)

```powershell
python -m app.simulate_cli           # compare les stratégies sur les villages observés
```

Hypothèses (optionnel) : `%LOCALAPPDATA%\CoCAutoFarm\simulation.json`, par exemple :

```json
{
  "capture_rates": {"gold": 0.75, "elixir": 0.75, "dark_elixir": 0.75},
  "attack_duration_s": 180,
  "army_ready_delay_s": 0,
  "search_cost_gold": 1500
}
```

## Phase 5 — Base de données

```powershell
python -m app.db_cli import           # importe les villages observés (sans doublon)
python -m app.db_cli stats            # résumé et statistiques par jour
python -m app.db_cli backup           # sauvegarde manuelle
```

Base : `%LOCALAPPDATA%\CoCAutoFarmutofarm.db` ; sauvegardes : `%LOCALAPPDATA%\CoCAutoFarmackups`.
Le mode observation enregistre désormais chaque village directement en base.

## Phase 5.2 — API locale

```powershell
python -m app.main                   # démarre l'API sur http://127.0.0.1:8765 (Ctrl+C pour arrêter)
```

- Documentation interactive : http://127.0.0.1:8765/docs → bouton **Authorize** → coller le jeton affiché au démarrage.
- L'API n'écoute que ce PC et exige le jeton (en-tête `Authorization: Bearer <jeton>`, ou `?token=` pour les images).
- Les réglages modifiés via `PUT /api/settings` sont enregistrés en base et utilisés par toutes les commandes.

## Phase 5.3 — Observation pilotée par l'API, logs

| URL | Rôle |
|---|---|
| `POST /api/observer/start` | démarre l'observation en tâche de fond (`{"interval_s": 1.0}` optionnel) |
| `POST /api/observer/stop` | l'arrête (le cycle en cours se termine) |
| `GET /api/observer` | état : analyses, villages enregistrés, dernier village, erreurs |
| `GET /api/logs` | derniers événements (`level`, `after_id` pour ne lire que les nouveaux) |

Journal complet (JSON, une ligne par événement) : `%LOCALAPPDATA%\CoCAutoFarm\logs\autofarm.log`.
`python -m app.observe_cli` utilise le même moteur que l'API.

## Phase 6 — Dashboard (React + TypeScript + Vite + Tailwind)

Deux terminaux :

```powershell
# Terminal 1 : le moteur
cd backend; .\.venv\Scripts\Activate.ps1; python -m app.main

# Terminal 2 : le dashboard (première fois : npm install)
cd frontend; npm run dev
```

Ouvrir l'URL « Dashboard » affichée par le moteur (`http://localhost:5173/?token=...`) : le jeton est pris en compte automatiquement.

```powershell
cd frontend
npm test              # tests (Vitest)
npm run typecheck     # vérification TypeScript
npm run build         # version de production (frontend/dist)
```

## Phase 7 — Application de bureau (Tauri 2)

Prérequis (une fois) : Rust (`rustup`, chaîne `stable-msvc`) et Visual Studio Build Tools 2022 (C++).

```powershell
cd desktop
npm install
npm run dev        # fenêtre de développement (lance aussi le serveur Vite du frontend)
npm run build      # version de production (desktop/src-tauri/target/release)
```

L'application démarre elle-même le moteur (port libre, jeton aléatoire) et l'arrête à la fermeture :
plus besoin de terminal ni de jeton. En développement (`npm run dev`), elle utilise le Python de `backend/.venv`.

`npm run build` enchaîne : moteur (PyInstaller, `pip install -r backend/requirements-build.txt` requis),
dashboard, application optimisée, puis installateur `src-tauri/target/release/bundle/nsis/*-setup.exe`.

Comportement de l'application installée :
- une seule instance : la relancer remet la fenêtre ouverte au premier plan ;
- taille et position de la fenêtre conservées d'un lancement à l'autre ;
- installateur en français, installé pour l'utilisateur courant (sans droits administrateur).
