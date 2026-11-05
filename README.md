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
