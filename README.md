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
```

- Images annotées : `%LOCALAPPDATA%\CoCAutoFarm\debug`.
- Captures d'entraînement : `datasets/*.png` (non versionnées) ; valeurs attendues : `datasets/labels.json` (versionné).
