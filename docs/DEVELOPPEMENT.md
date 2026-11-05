# CoC AutoFarm — guide de développement

Pour les personnes qui modifient le code. Le guide utilisateur est le [README](../README.md).
Cahier des charges : [CLAUDE.md](../CLAUDE.md) · Choix techniques : [ARCHITECTURE.md](ARCHITECTURE.md).

## Organisation

| Dossier | Contenu |
|---|---|
| `backend/` | moteur Python : capture, vision, analyse, stratégies, base SQLite, API FastAPI |
| `frontend/` | interface React + TypeScript + Vite + Tailwind |
| `desktop/` | application Windows (Tauri 2), scripts de compilation et de publication |
| `tests/` | tests du moteur (pytest) |
| `datasets/` | captures annotées (images non versionnées, `labels.json` versionné) |

## Installation de l'environnement (une fois)

- Python 3.11, Node.js 20+, Rust (`rustup`, chaîne `stable-msvc`), Visual Studio Build Tools 2022 (C++).
- GitHub CLI pour publier : `winget install GitHub.cli`, puis `gh auth login`.

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-build.txt
cd ..\frontend; npm install
cd ..\desktop; npm install
```

## Lancer en développement

```powershell
cd desktop
npm run dev          # fenêtre de l'application ; lance le moteur (Python du venv) et le serveur Vite
```

Sans la fenêtre de bureau (navigateur) : `python -m app.main` dans `backend\` (venv activé), puis
`npm run dev` dans `frontend\`, et ouvrir l'URL « Dashboard » affichée par le moteur (le jeton est dans l'URL).

## Tests

```powershell
cd backend; .\.venv\Scripts\Activate.ps1; python -m pytest ..\tests     # moteur
cd frontend; npm test; npm run typecheck                                  # interface
cd desktop\src-tauri; cargo test                                          # partie Rust
```

`tests/test_resolutions.py` relit les captures annotées à plusieurs tailles de fenêtre
(960x540 à 2560x1440) ; il est ignoré si les images de `datasets/` sont absentes.

## Outils en ligne de commande (dans `backend\`, venv activé)

| Commande | Rôle |
|---|---|
| `python -m app.capture_cli` | capture la fenêtre du jeu (`--full` : tout l'écran) |
| `python -m app.vision_debug` | écran reconnu + ressources lues sur la dernière capture |
| `python -m app.build_templates` | régénère les modèles de reconnaissance après ajout de captures annotées |
| `python -m app.observe_cli` | mode observation en terminal (Ctrl+C pour arrêter) |
| `python -m app.analyze_cli [--explain N]` | classe les villages observés par score |
| `python -m app.simulate_cli` | compare les stratégies sur les villages observés |
| `python -m app.db_cli import / stats / backup` | import des observations, statistiques, sauvegarde |
| `python -m app.main` | moteur + API sur http://127.0.0.1:8765 (documentation : `/docs`, bouton Authorize + jeton affiché) |

## Données utilisateur

Tout est dans `%LOCALAPPDATA%\CoCAutoFarm\` : `autofarm.db` (base), `backups\`, `screenshots\`,
`observations\`, `debug\`, `logs\autofarm.log` (JSON, une ligne par événement).
Les réglages sont en base (`PUT /api/settings`, modification partielle).

## API locale (principales routes)

| Route | Rôle |
|---|---|
| `GET /api/status` | état du moteur, version, `schema_version` de la base |
| `GET /api/villages`, `GET /api/villages/{id}` | historique (filtres, tri) et fiche d'un village |
| `GET /api/statistics`, `GET /api/strategies/compare` | statistiques, comparaison des stratégies |
| `GET/PUT /api/settings` | réglages (modification partielle) |
| `POST /api/observer/start` / `stop`, `GET /api/observer` | observation |
| `GET /api/logs` | derniers événements |
| `POST /api/database/backup?label=` | sauvegarde de la base |
| `POST /api/alerts/test` | alerte d'exemple (son + notification selon les réglages) |
| `POST /api/shutdown` | arrêt propre (utilisé par l'application de bureau) |

L'API n'écoute que `127.0.0.1` et exige le jeton (`Authorization: Bearer <jeton>`, ou `?token=` pour les images).

## Compilation et publication

Clé de signature des mises à jour : `%USERPROFILE%\.coc-autofarm\updater.key` + `updater.password`,
**hors du dépôt, à sauvegarder** (sans elle, les installations existantes ne peuvent plus être mises à jour).

```powershell
cd desktop
.\scripts\build-release.ps1                                  # installateur signé seul (pas de publication)
.\scripts\release.ps1 -Version 0.3.0 -DryRun                 # essai complet de publication, rien n'est publié
.\scripts\release.ps1 -Version 0.3.0                         # publication stable
.\scripts\release.ps1 -Version 0.3.0-beta.1 -Prerelease      # bêta (canal bêta uniquement)
```

Avant de publier : noter les changements dans `CHANGELOG.md` sous `## <version> — en développement`
(ce texte devient les notes de version) et tout commiter. Le script vérifie le dépôt, écrit la version
dans les 6 fichiers concernés, lance tous les tests, compile et signe, prépare `releases\v<version>\`
(installateur, `latest.json`, notes), commite, pose le tag, pousse, crée la release GitHub et met à jour
le canal bêta (release technique `updater-beta`).

## Identité visuelle

`desktop/branding/` : `icon.svg` (source de l'icône), `icon-1024.png`, images de l'installateur
(`installer-sidebar.bmp` 164x314, `installer-header.bmp` 150x57, générées depuis les fichiers HTML voisins).
Après modification de l'icône : `npx tauri icon branding/icon-1024.png` dans `desktop\` (ne garder que
les icônes Windows), et remplacer `frontend/src/assets/logo.png` (256 px).
