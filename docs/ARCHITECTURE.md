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
- Migrations SQLite + sauvegarde automatique avant migration (voir §8).

## 5. Arborescence

Celle du cahier des charges (§12), avec en plus `docs/`. `backend/app/` contient `capture/ vision/ analysis/ strategy/ database/ api/`; `tests/` à la racine.

## 6. Feuille de route

Phases 1–9 du cahier des charges. Estimation : P1 (≈1 sem.), P2 vision (2–4 sem., dépend des captures réelles), P3–4 (2 sem.), P5 (1 sem.), P6 (2–3 sem.), P7–8 (2–3 sem.), P9 (1–2 sem.). L'updater est testé tôt (dès un « hello world » Tauri) pour limiter les risques.

## 7. Vision — décisions (phase 2)

- **Capture** : `PrintWindow` (fenêtre recouverte acceptée), repli sur capture d'écran si image noire.
- **Zones relatives** (fractions de l'image) mesurées sur captures réelles 1323x744.
- **Chiffres et écrans** : template matching OpenCV (corrélation normalisée), modèles générés depuis `datasets/labels.json` par `app.build_templates` et livrés avec l'application.
- **E/S d'images via Pillow** : `cv2.imread/imwrite` échouent silencieusement sur les chemins accentués sous Windows.
- **Bâtiments (reporté)** : le butin est déjà lu directement, suffisant pour un premier score (phase 3). Les écrans de recherche sont collectés automatiquement par le mode observation ; la détection des bâtiments viendra ensuite avec **Ultralytics YOLO** (export ONNX, inférence `onnxruntime`). Sa licence AGPL-3.0 implique de publier le code source de CoC AutoFarm sous une licence compatible : accepté par le porteur du projet (2026-11-05).

## 8. Base de données — décisions (phase 5)

- SQLite + SQLAlchemy 2.0, fichier `%LOCALAPPDATA%\CoCAutoFarmutofarm.db` (mode WAL, clés étrangères actives).
- **Migrations maison** (`database/migrations.py`) plutôt qu'Alembic : numéro de version dans `PRAGMA user_version`, scripts SQL appliqués dans l'ordre, chacun dans une transaction. Plus simple à comprendre et à embarquer avec PyInstaller. Une migration publiée n'est jamais modifiée.
- Sauvegarde automatique avant toute migration d'une base existante (`backups/`, 5 dernières conservées). Une base plus récente que le logiciel est refusée (pas de retour arrière silencieux).
- Un test vérifie que `models.py` correspond exactement au schéma produit par les migrations.
- Le mode observation enregistre directement en base ; `db_cli import` importe les observations JSON existantes (sans doublon).

## 9. Application de bureau — décisions (phase 7)

- Moteur embarqué : PyInstaller en mode **onedir** (`backend.exe` + `_internal/`, ~180 Mo, démarrage ~1 s), livré comme **ressource** Tauri (`bundle.resources`) plutôt que `externalBin`, qui ne gère qu'un fichier unique.
- Lancement par Rust (`src-tauri/src/backend.rs`) : port libre choisi par le système, jeton de 32 octets aléatoires, transmis au moteur par variable d'environnement et au dashboard par la commande `backend_config`. Pas de console (CREATE_NO_WINDOW).
- Arrêt : `POST /api/shutdown` à la fermeture, arrêt forcé après 8 s. Le moteur surveille aussi le processus parent (`--parent-pid`) : il s'arrête si l'application disparaît brutalement.
- En développement, la même logique lance `python -m app.main` du venv ; la configuration de production (`tauri.release.conf.json`) ajoute la construction du moteur et sa copie dans l'installateur.
- CSP de la fenêtre : connexions limitées à `127.0.0.1`.
- Instance unique (`tauri-plugin-single-instance`, enregistré en premier) : relancer l'application remet la fenêtre existante au premier plan, sans démarrer un second moteur sur la même base SQLite.
- Géométrie de la fenêtre (`tauri-plugin-window-state`) : taille, position et état agrandi sauvegardés dans `%APPDATA%\com.thomaslrpn.cocautofarm\.window-state.json`.
- Installateur NSIS en français, installation par utilisateur (`%LOCALAPPDATA%\CoC AutoFarm`, pas de droits administrateur).

## 10. Mises à jour — décisions (phase 8)

- `tauri-plugin-updater` : lit `https://github.com/thomaslrpn/CocFarmAuto/releases/latest/download/latest.json`, compare les versions (SemVer), télécharge l'installateur NSIS et vérifie sa signature minisign avec la clé publique de `tauri.conf.json`. Installation en mode `passive` (barre de progression, sans questions), relance automatique.
- Clé privée hors dépôt (`%USERPROFILE%\.coc-autofarm\`), lue seulement par `desktop/scripts/build-release.ps1` le temps de la compilation. `createUpdaterArtifacts` n'est activé que dans `tauri.release.conf.json` (le mode dev n'a pas besoin de la clé).
- Ordre d'installation, du plus sûr au plus risqué : téléchargement → sauvegarde de la base (`POST /api/database/backup`, API de sauvegarde SQLite, cohérente même en écriture) → arrêt du moteur (`prepare_update`, car l'installateur remplace `backend.exe`) → installation. Échec avant l'arrêt du moteur : rien n'a changé, « Réessayer ». Après : bouton « Redémarrer l'application ».
- Les données utilisateur (`%LOCALAPPDATA%\CoCAutoFarm`) sont séparées du dossier d'installation : l'installateur ne les touche jamais ; les migrations de schéma gardent leur propre sauvegarde.
- Publication : `desktop/scripts/release.ps1` (GitHub CLI). Version unique écrite dans 6 fichiers (`tests/test_version.py` vérifie la cohérence). Les notes de version sont la section correspondante de `CHANGELOG.md`. L'installateur est renommé sans espace (`CoC-AutoFarm_<v>_x64-setup.exe`) car GitHub remplace les espaces des pièces jointes. En cas d'essai (`-DryRun`) ou d'échec avant le commit, les fichiers modifiés sont restaurés depuis leur contenu d'origine (pas de `git checkout`).
- Canal stable = `releases/latest` de GitHub, qui ignore les pre-releases : une bêta publiée avec `-Prerelease` n'atteint jamais les utilisateurs stables.
- Canaux (phase 8.3) : réglage `app.update_channel` (stable / beta) stocké en base comme les autres préférences. La vérification passe par la commande Rust `check_update(channel)` (`src-tauri/src/updates.rs`), qui interroge le `latest.json` du canal et renvoie les mêmes métadonnées que le plugin : le téléchargement, la vérification de signature et l'installation restent ceux du plugin. Canal bêta = release technique `updater-beta` (pre-release), alimentée par `release.ps1` à chaque publication tant que sa version ne recule pas. Le canal « développement » du cahier des charges correspond au mode `npm run dev` (pas de publication).
- `app.auto_check_updates` désactive la vérification automatique (le bouton manuel reste disponible). Historique des versions : API publique GitHub (`connect-src https://api.github.com` dans la CSP), sans compte.
- Retour bêta → stable : avec une pré-version installée et le canal stable choisi, `check_update` propose la dernière stable même plus ancienne (`Channel::should_offer`). Compatibilité : `latest.json` porte `schema_version` (migrations connues par cette version), `/api/status` donne celle de la base ; si la version proposée en connaît moins, le retour est bloqué (elle refuserait d'ouvrir la base) et l'utilisateur attend la stable suivante. Publication antérieure sans ce champ : retour autorisé avec avertissement (sauvegarde faite avant).

## 11. Version 1.0 — décisions (phase 9)

- Tailles de fenêtre : les zones sont proportionnelles ; pour une fenêtre plus petite que la référence (744 px de haut), la zone d'un compteur est agrandie (Lanczos) à l'échelle de référence avant la découpe des chiffres, pour que les seuils en pixels restent valables. Mesuré sur les 15 captures annotées redimensionnées : lecture exacte (écrans et 60 valeurs) de 960x540 à 2560x1440 (`tests/test_resolutions.py`) ; 800x450 échoue (chiffres de 8 px) d'où le minimum 960x540, signalé dans les logs. Formats autres que 16:9 non mesurés (pas de capture réelle).
- Licence : GNU AGPL v3 (imposée par Ultralytics YOLO, prévu pour la détection des bâtiments). Texte officiel dans `LICENSE`, affiché par l'installateur.
- Identité : icône originale (pièce d'or + loupe, aucun élément du jeu), `desktop/branding/`. Fond de fenêtre sombre dès l'ouverture (pas de flash blanc avant l'écran de démarrage).
- Documentation : README = guide utilisateur ; `docs/DEVELOPPEMENT.md` = guide de développement.

## 12. Pendant le jeu — mini-fenêtre et alertes

- Les alertes partent du moteur, pas de l'interface : une fenêtre WebView cachée derrière le jeu ou réduite voit ses minuteries ralenties (jusqu'à une fois par minute), elle raterait des villages. `app/alerts.py` est branché sur `on_village` de l'observation et relit les réglages à chaque village.
- Son : carillon propre à l'application (`backend/app/assets/alert.wav`, généré par `make_alert_sound.py`), joué par `winsound` (module standard Windows) dans le moteur. Notification Windows désactivée par défaut (le son suffit). Notification : le moteur écrit `COCAF-EVENT {json}` sur sa sortie standard (UTF-8 forcé par `PYTHONIOENCODING`) ; `src-tauri/src/events.rs` la lit en continu dans un fil dédié et affiche une notification Windows silencieuse (`tauri-plugin-notification`), le son restant un réglage séparé. Un protocole par sortie standard évite un second serveur ou un sondage HTTP côté Rust.
- Mini-fenêtre : seconde fenêtre Tauri `overlay` (toujours au-dessus, hors barre des tâches) créée par la commande `toggle_overlay` ; même application React, qui affiche `OverlayPage` quand le libellé de la fenêtre est `overlay` (pas de menu ni de vérification des mises à jour). Elle sonde `GET /api/observer` chaque seconde : toujours visible, elle n'est pas ralentie. Fermer la fenêtre principale ferme l'application entière.
- Ni l'une ni l'autre n'agit sur le jeu (aucun clic, aucune touche) : le cahier des charges exclut l'automatisation des combats.

## 13. Récapitulatif d'attaque

- Pendant un combat, le jeu affiche le « Butin disponible » RESTANT (même zone que pendant la recherche, déjà lue par la vision) : récupéré = butin au départ − butin restant à la fin. Aucun nouvel élément visuel à reconnaître.
- `app/attacks.py` (`AttackTracker`) suit l'écran confirmé image par image. Départ = butin lu pendant la recherche si le combat la suit de moins de 3 minutes (sinon première lecture fiable du combat, attaque non rattachée à un village). Fin = l'écran de combat disparaît (changement confirmé sur 2 images).
- Robustesse : seules les lectures de confiance ≥ 0,6 comptent ; une lecture supérieure au butin de départ est ignorée ; le butin restant est la dernière valeur lue au moins deux fois parmi les 5 dernières (une lecture isolée faussée par un sort est écartée), sinon la dernière lecture.
- Stockage : table `attacks` (migration 2, `schema_version` 2), liée au village (`ON DELETE SET NULL`). Exposé par `GET /api/observer` (`last_attack`) et `GET /api/villages/{id}` (`attack`).
- Note du farm (`rate_attack`) : `compute_profitability` appliqué au butin récupéré (une ressource non lue compte 0), avec les réglages au moment de la fin du combat ; appréciation excellent / bon / moyen / faible sur les seuils des recommandations. Colonnes ajoutées par la migration 3 (la migration 2 avait déjà été appliquée par une version de test : jamais modifier une migration appliquée). Attaques plus anciennes sans note : notées à l'affichage avec les réglages actuels.

## 14. Ressource prioritaire

- Poids : équilibré 40/40/20 (inchangé) ; ressource prioritaire 80 %, les deux autres 10 % (auparavant 60/20/20). Constat sur des villages réels avec l'élixir noir prioritaire : or et élixir au maximum donnaient déjà 40 points, d'où des villages pauvres en élixir noir classés « intéressant ». Désormais, sans la ressource prioritaire, un village plafonne à 20/100.
- Mini-fenêtre : priorité et butin visé de cette ressource modifiables (`PUT /api/settings`) ; `ObserverService.rescore_last_village` recalcule le village affiché (affichage seulement, l'historique garde le score de son analyse).
