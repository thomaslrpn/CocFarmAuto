"""Point d'entrée de l'exécutable embarqué `backend.exe` (construit par PyInstaller).

En développement, on lance plutôt `python -m app.main` : même code.
"""
from app.main import main

if __name__ == "__main__":
    raise SystemExit(main())
