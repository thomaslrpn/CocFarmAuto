# -*- mode: python ; coding: utf-8 -*-
"""Recette PyInstaller du moteur : `python -m PyInstaller --noconfirm backend.spec`.

Résultat : dist/backend/backend.exe + dist/backend/_internal/ (Python + dépendances).
Mode « onedir » (un dossier) plutôt qu'un seul .exe : démarrage plus rapide
(rien à décompresser à chaque lancement) et moins de faux positifs antivirus.
"""
import os

from PyInstaller.utils.hooks import collect_submodules

ROOT = SPECPATH  # dossier de ce fichier (backend/)

a = Analysis(
    [os.path.join(ROOT, "run_backend.py")],
    pathex=[ROOT],
    # Modèles de reconnaissance livrés avec l'application (chiffres, écrans).
    datas=[
        (os.path.join(ROOT, "app", "vision", "templates"), os.path.join("app", "vision", "templates")),
        (os.path.join(ROOT, "app", "assets", "alert.wav"), os.path.join("app", "assets")),  # son des alertes
    ],
    # uvicorn charge certains modules dynamiquement (boucle, protocoles) : on les inclut tous.
    hiddenimports=collect_submodules("uvicorn"),
    excludes=["tkinter", "pytest", "matplotlib", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="backend",
    console=True,  # sorties visibles en développement ; l'application le lance sans fenêtre
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="backend", upx=False)
