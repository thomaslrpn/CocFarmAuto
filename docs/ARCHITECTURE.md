# Architecture CoC AutoFarm — décisions

> Outil d'analyse / aide à la décision / simulation. Il n'automatise pas les combats et ne contourne pas les protections du jeu.

## 1. Architecture technique

```
┌──────────── Tauri (shell Rust, WebView2) ────────────┐
│  Frontend React/TS/Vite/Tailwind (build statique)    │
│        │ HTTP 127.0.0.1:<port aléatoire> + token     │
│  Sidecar : backend Python (FastAPI) en .exe          │
│        capture → vision → analysis → strategy → DB   │
└──────────────────────────────────────────────────────┘
Données utilisateur : %LOCALAPPDATA%\CoCAutoFarm (SQLite, captures, logs)
```
- Tauri lance le backend comme **sidecar**, choisit un port libre, passe un token de session, et le tue à la fermeture.
- Chaque module backend (capture, vision, analysis, strategy, database, api) est indépendant, testable seul, et communique via des modèles Pydantic.
- Données utilisateur strictement séparées du dossier d'installation (jamais écrasées par une MAJ).

## 2. Tauri vs Electron

| Critère | Tauri | Electron |
|---|---|---|
| Taille installateur | ~5–10 Mo (+ backend) | ~80–150 Mo (+ backend) |
| RAM | faible (WebView2 natif) | élevée (Chromium embarqué) |
| Sidecar Python | supporté nativement | à gérer à la main |
| Updater signé | plugin officiel (signature minisign) | electron-updater |
| Courbe d'apprentissage | Rust minimal nécessaire (peu de code) | 100 % JS |

**Décision : Tauri.** Le Rust requis se limite à la config du sidecar et de l'updater. Repli sur Electron seulement si WebView2 pose problème.

## 3. Embarquer Python

- **PyInstaller (mode onedir)** pour produire `backend.exe` : mature, bien documenté. Nuitka reste une optimisation possible plus tard.
- Sidecar Tauri (`externalBin`), version Python 3.11 figée dans le build.
- Aucun Python/Node requis chez l'utilisateur final.

## 4. Mises à jour

- **Tauri updater plugin + GitHub Releases** : `latest.json` + installateur signé (clé minisign).
- La clé **privée** reste sur la machine de build / secret CI, jamais dans le dépôt (`.gitignore`). Seule la clé publique est embarquée.
- Canaux : stable / beta / dev = différents `latest.json` (ex. tags `v1.1.0`, `v1.2.0-beta.1`).
- Installateur : NSIS (généré par Tauri), raccourcis bureau + menu Démarrer + désinstalleur.
- Migrations SQLite (Alembic) + sauvegarde automatique avant migration.

## 5. Arborescence

Celle du cahier des charges (§12), avec en plus `docs/`. `backend/app/` contient `capture/ vision/ analysis/ strategy/ database/ api/`; `tests/` à la racine.

## 6. Feuille de route

Phases 1–9 du cahier des charges. Estimation : P1 (≈1 sem.), P2 vision (2–4 sem., dépend des captures réelles), P3–4 (2 sem.), P5 (1 sem.), P6 (2–3 sem.), P7–8 (2–3 sem.), P9 (1–2 sem.). L'updater est testé tôt (dès un « hello world » Tauri) pour limiter les risques.
