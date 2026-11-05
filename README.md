<p align="center">
  <img src="desktop/branding/icon-1024.png" width="120" alt="">
</p>

<h1 align="center">CoC AutoFarm</h1>

<p align="center">
  Repère les villages rentables pendant que tu farmes sur Clash of Clans.<br>
  Pour Windows, avec Google Play Games.
</p>

<p align="center">
  <a href="https://github.com/thomaslrpn/CocFarmAuto/releases/latest"><b>⬇ Télécharger la dernière version</b></a>
</p>

---

## Ce que fait CoC AutoFarm

Pendant que tu cherches des adversaires dans Clash of Clans, CoC AutoFarm regarde l'écran du jeu et,
pour chaque village rencontré :

- lit le **butin disponible** (or, élixir, élixir noir) ;
- calcule un **score de rentabilité sur 100**, expliqué ligne par ligne ;
- te dit s'il est **très intéressant**, **intéressant**, **moyen** ou **à passer** ;
- recommande une **stratégie** (farm or, élixir, élixir noir ou équilibré) ;
- garde un **historique** et des **statistiques** de tous les villages vus.

**CoC AutoFarm ne joue pas à ta place.** Il ne clique sur rien, n'envoie aucune action au jeu et ne
contourne aucune protection : il observe et te conseille, c'est toi qui décides et qui attaques.

## Configuration requise

- Windows 10 ou 11 (64 bits).
- [Google Play Games pour PC](https://play.google.com/googleplaygames) avec Clash of Clans installé.
- Fenêtre du jeu d'au moins **960 × 540** pixels (plein écran ou fenêtre, format 16:9).
- Environ 200 Mo d'espace disque. Internet sert uniquement aux mises à jour.

## Installation

1. [Télécharge l'installateur](https://github.com/thomaslrpn/CocFarmAuto/releases/latest)
   (fichier `CoC-AutoFarm_…_x64-setup.exe`).
2. Lance-le et suis les étapes. Aucun droit administrateur n'est demandé.
3. Si Windows affiche « Windows a protégé votre ordinateur », clique sur **Informations complémentaires**
   puis **Exécuter quand même**. Cet avertissement apparaît parce que le logiciel est récent et n'a pas
   de certificat payant ; le code source est public sur cette page.

CoC AutoFarm apparaît ensuite sur le bureau et dans le menu Démarrer.

## Utilisation

1. Lance **Clash of Clans** dans Google Play Games.
2. Lance **CoC AutoFarm**.
3. Sur le **Dashboard**, clique sur **Démarrer l'observation**.
4. Dans le jeu, cherche des adversaires comme d'habitude. Chaque village affiché est analysé
   automatiquement en quelques secondes.
5. Regarde la recommandation dans CoC AutoFarm, puis attaque ou passe au village suivant.

Les pages de l'application :

| Page | Ce que tu y trouves |
|---|---|
| **Dashboard** | nombre de villages vus, butin repéré, score moyen, derniers villages |
| **Analyse** | le dernier village : capture, butin lu, score détaillé, stratégie conseillée |
| **Historique** | tous les villages, avec recherche, filtres et tri |
| **Statistiques** | évolution du rendement, répartition des ressources, comparaison des stratégies |
| **Paramètres** | ressource prioritaire, butin visé, coût de ton armée, fréquence d'analyse, mises à jour |
| **Logs** | ce que fait le logiciel, en direct (utile en cas de problème) |
| **À propos** | version, nouveautés, mises à jour |

### Bien régler le score

Dans **Paramètres**, indique :
- ta **ressource prioritaire** (or, élixir, élixir noir ou équilibré) ;
- le **butin que tu vises** par attaque : un village qui l'atteint obtient la note maximale ;
- le **coût de ton armée** : il est déduit du butin pour juger si l'attaque vaut le coup.

Les nouveaux réglages s'appliquent aux villages analysés ensuite.

## Mises à jour

CoC AutoFarm vérifie tout seul s'il existe une nouvelle version (au démarrage, puis toutes les 6 heures).
Quand c'est le cas, un encadré apparaît en bas du menu : va dans **À propos** et clique sur
**Installer et redémarrer**. Tes données sont sauvegardées avant chaque mise à jour et ne sont jamais effacées.

Dans **Paramètres**, tu peux :
- choisir le canal **Stable** (recommandé) ou **Bêta** pour essayer les nouveautés en avant-première ;
- désactiver la recherche automatique (le bouton de la page À propos reste disponible).

Pour quitter la bêta, repasse sur **Stable** et clique sur **Revenir à la version stable** dans À propos.

## Tes données

Tout reste sur ton PC, dans `%LOCALAPPDATA%\CoCAutoFarm` (copie ce chemin dans l'Explorateur Windows) :
historique des villages, captures, réglages, sauvegardes et journaux. Rien n'est envoyé sur internet.
Chaque utilisateur de l'ordinateur a ses propres données.

## Désinstaller

**Paramètres Windows → Applications → Applications installées → CoC AutoFarm → Désinstaller.**
Ton historique est conservé dans `%LOCALAPPDATA%\CoCAutoFarm` ; supprime ce dossier si tu veux tout effacer.

## Problèmes fréquents

**« Fenêtre du jeu introuvable »**
Clash of Clans doit être lancé dans Google Play Games et la fenêtre ne doit pas être réduite.

**Les montants lus sont faux ou absents**
Agrandis la fenêtre du jeu (au moins 960 × 540, plein écran conseillé). La page **Logs** signale une
fenêtre trop petite.

**« Le moteur d'analyse n'a pas pu démarrer »**
Ferme puis relance CoC AutoFarm. Si le problème continue, le détail est dans
`%LOCALAPPDATA%\CoCAutoFarm\logs\autofarm.log`.

## Limites actuelles

- Seul le butin est analysé : la défense du village (hôtel de ville, défenses, réserves) n'est pas encore
  reconnue. C'est prévu dans une prochaine version.
- Testé avec une fenêtre au format 16:9.

## Licence

Logiciel libre sous licence [GNU AGPL v3](LICENSE). Pour contribuer ou compiler le projet :
[guide de développement](docs/DEVELOPPEMENT.md). Clash of Clans est une marque de Supercell ;
CoC AutoFarm est un projet indépendant, ni affilié ni approuvé par Supercell.
