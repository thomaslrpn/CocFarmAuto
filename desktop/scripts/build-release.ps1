# Compile la version de production SIGNÉE de CoC AutoFarm.
#
# Produit dans src-tauri\target\release\bundle\nsis\ :
#   - CoC AutoFarm_<version>_x64-setup.exe      installateur
#   - CoC AutoFarm_<version>_x64-setup.exe.sig  signature (vérifiée par les mises à jour)
#
# La clé privée de signature n'est JAMAIS dans le dépôt. Elle est lue dans :
#   %USERPROFILE%\.coc-autofarm\updater.key       (clé privée)
#   %USERPROFILE%\.coc-autofarm\updater.password  (son mot de passe)
# Sauvegarde ces deux fichiers : sans eux, les installations existantes ne pourront
# plus recevoir de mises à jour.
#
# Usage (depuis desktop\) :  .\scripts\build-release.ps1

$ErrorActionPreference = "Stop"
$keyDir = Join-Path $env:USERPROFILE ".coc-autofarm"
$keyFile = Join-Path $keyDir "updater.key"
$passwordFile = Join-Path $keyDir "updater.password"

foreach ($file in @($keyFile, $passwordFile)) {
    if (-not (Test-Path $file)) { throw "Fichier de signature introuvable : $file" }
}

# Variables lues par `tauri build` (uniquement pour ce processus, rien n'est enregistré).
$env:TAURI_SIGNING_PRIVATE_KEY = (Get-Content -Raw $keyFile).Trim()
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = (Get-Content -Raw $passwordFile).Trim()

try {
    Push-Location (Join-Path $PSScriptRoot "..")
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "La compilation a échoué (code $LASTEXITCODE)." }
    Get-ChildItem "src-tauri\target\release\bundle\nsis" -Filter "*-setup.exe*" |
        Select-Object Name, @{ n = "Taille (Mo)"; e = { [math]::Round($_.Length / 1MB, 1) } }
}
finally {
    Pop-Location
    Remove-Item Env:TAURI_SIGNING_PRIVATE_KEY, Env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD -ErrorAction SilentlyContinue
}
