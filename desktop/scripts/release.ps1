#Requires -Version 7
<#
.SYNOPSIS
  Publie une nouvelle version de CoC AutoFarm sur GitHub Releases.

.DESCRIPTION
  Étapes :
    1. Vérifications (version SemVer, dépôt propre sur main, tag libre, changelog, GitHub CLI).
    2. Numéro de version écrit partout + date dans CHANGELOG.md.
    3. Tests automatiques (backend + frontend).
    4. Compilation signée (build-release.ps1).
    5. Préparation dans releases\v<version>\ : installateur, latest.json, notes de version.
    6. Commit « Version x.y.z », tag vx.y.z, push, puis création de la release GitHub.
    7. Mise à jour du canal bêta (release technique « updater-beta »).

  Canaux (choisis dans les Paramètres de l'application) :
    - stable : .../releases/latest/download/latest.json. GitHub ignore les pre-releases,
      donc une version publiée avec -Prerelease n'est PAS vue par le canal stable ;
    - bêta   : .../releases/download/updater-beta/latest.json, remplacé à chaque
      publication (stable ou bêta) sauf si le canal bêta a déjà une version plus récente.

.EXAMPLE
  .\scripts\release.ps1 -Version 0.1.1                      # publication stable
  .\scripts\release.ps1 -Version 0.2.0-beta.1 -Prerelease   # bêta
  .\scripts\release.ps1 -Version 0.2.0 -DryRun              # essai complet, rien n'est publié
#>
param(
    [Parameter(Mandatory)] [string] $Version,
    [switch] $Prerelease, # version bêta : invisible pour le canal stable
    [switch] $DryRun,     # tout sauf commit / push / release (fichiers de version restaurés)
    [switch] $SkipTests
)

$ErrorActionPreference = "Stop"
$Repo = "thomaslrpn/CocFarmAuto"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Tag = "v$Version"
$BetaTag = "updater-beta" # release technique qui porte le latest.json du canal bêta
$BetaLatestUrl = "https://github.com/$Repo/releases/download/$BetaTag/latest.json"
$Utf8 = [Text.UTF8Encoding]::new($false) # UTF-8 sans BOM

# Fichiers contenant le numéro de version : chemin -> motif (le 1er groupe est conservé).
$VersionFiles = [ordered]@{
    "backend\app\config.py"             = '(APP_VERSION = )"[^"]+"'
    "desktop\src-tauri\tauri.conf.json" = '("version": )"[^"]+"'
    "desktop\src-tauri\Cargo.toml"      = '(?m)(^version = )"[^"]+"'
    "desktop\src-tauri\Cargo.lock"      = '(name = "coc-autofarm"\r?\nversion = )"[^"]+"'
    "desktop\package.json"              = '("version": )"[^"]+"'
    "frontend\package.json"             = '("version": )"[^"]+"'
}

function Step([string] $message) { Write-Host "`n==> $message" -ForegroundColor Cyan }

function Assert-Native([string] $what) {
    if ($LASTEXITCODE -ne 0) { throw "$what a échoué (code $LASTEXITCODE)." }
}

function Read-Text([string] $relative) { [IO.File]::ReadAllText((Join-Path $Root $relative), $Utf8) }
function Write-Text([string] $relative, [string] $text) { [IO.File]::WriteAllText((Join-Path $Root $relative), $text, $Utf8) }

function Get-CurrentVersion {
    $match = [regex]::Match((Read-Text "backend\app\config.py"), 'APP_VERSION = "([^"]+)"')
    if (-not $match.Success) { throw "APP_VERSION introuvable dans backend\app\config.py" }
    $match.Groups[1].Value
}

# Contenu d'origine des fichiers modifiés : remis en place après un essai ou un échec
# (sans git, donc sans risque pour d'éventuelles modifications en cours).
$Originals = [ordered]@{}

function Update-File([string] $relative, [string] $newText) {
    if (-not $script:Originals.Contains($relative)) { $script:Originals[$relative] = Read-Text $relative }
    Write-Text $relative $newText
}

function Restore-Files {
    foreach ($entry in $script:Originals.GetEnumerator()) { Write-Text $entry.Key $entry.Value }
    $script:Originals.Clear()
}

function Set-ProjectVersion([string] $newVersion) {
    foreach ($entry in $VersionFiles.GetEnumerator()) {
        $text = Read-Text $entry.Key
        $regex = [regex]::new($entry.Value)
        if (-not $regex.IsMatch($text)) { throw "Version introuvable dans $($entry.Key)" }
        Update-File $entry.Key $regex.Replace($text, "`${1}`"$newVersion`"", 1)
    }
    # « ## 0.1.1 — en développement » devient « ## 0.1.1 — 2026-11-05 ».
    $heading = [regex]::new("(?m)^## $([regex]::Escape($newVersion))\b[^\r\n]*")
    Update-File "CHANGELOG.md" $heading.Replace((Read-Text "CHANGELOG.md"), "## $newVersion — $(Get-Date -Format 'yyyy-MM-dd')", 1)
}

# Canal bêta : publie ce latest.json dans la release technique, sauf si elle annonce
# déjà une version plus récente (ex. une bêta 0.3.0-beta.1 après une stable 0.2.1).
function Update-BetaChannel([string] $latestJson, [System.Management.Automation.SemanticVersion] $newVersion) {
    try {
        $currentBeta = [System.Management.Automation.SemanticVersion] (Invoke-RestMethod $BetaLatestUrl).version
    }
    catch {
        $currentBeta = $null # pas encore de canal bêta
    }
    if ($currentBeta -and $currentBeta -gt $newVersion) {
        Write-Host "Canal bêta inchangé : il annonce déjà $currentBeta."
        return
    }
    gh release view $BetaTag --repo $Repo *> $null
    if ($LASTEXITCODE -ne 0) {
        gh release create $BetaTag --repo $Repo --prerelease --target main --title "Canal bêta (fichier technique)" `
            --notes "Contient le latest.json lu par les applications réglées sur le canal bêta. Ce n'est pas une version : rien à télécharger ici."
        Assert-Native "Création de la release $BetaTag"
    }
    gh release upload $BetaTag $latestJson --clobber --repo $Repo
    Assert-Native "Mise à jour du canal bêta"
    Write-Host "Canal bêta : $newVersion"
}

function Get-ReleaseNotes([string] $forVersion) {
    $lines = (Read-Text "CHANGELOG.md") -split "\r?\n"
    $start = [Array]::FindIndex($lines, [Predicate[string]] { param($l) $l -match "^## $([regex]::Escape($forVersion))\b" })
    $notes = foreach ($line in $lines[($start + 1)..($lines.Length - 1)]) {
        if ($line -match "^## ") { break }
        $line
    }
    ($notes -join "`n").Trim()
}

Push-Location $Root
try {
    # ------------------------------------------------------------------ 1. Vérifications
    Step "Vérifications"
    $semver = $null
    if (-not [System.Management.Automation.SemanticVersion]::TryParse($Version, [ref] $semver)) {
        throw "« $Version » n'est pas une version SemVer (ex. 1.2.3 ou 1.3.0-beta.1)."
    }
    $current = [System.Management.Automation.SemanticVersion] (Get-CurrentVersion)
    if ($semver -lt $current) { throw "La version $Version est plus ancienne que la version actuelle ($current)." }

    if ((git branch --show-current) -ne "main") { throw "Publie depuis la branche main." }
    if (git status --porcelain) {
        if (-not $DryRun) { throw "Le dépôt contient des modifications non commitées : commite-les d'abord." }
        Write-Warning "Modifications non commitées : accepté en mode essai uniquement."
    }
    if (git tag -l $Tag) { throw "Le tag $Tag existe déjà : cette version a déjà été publiée." }
    if ($semver -eq $current -and (git tag -l "v*")) {
        throw "La version $Version est déjà la version actuelle : choisis un numéro supérieur."
    }
    if (-not ((Read-Text "CHANGELOG.md") -match "(?m)^## $([regex]::Escape($Version))\b")) {
        throw "Ajoute d'abord une section « ## $Version — en développement » dans CHANGELOG.md (elle sert de notes de version)."
    }
    if (-not $DryRun) {
        if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
            throw "GitHub CLI introuvable : winget install GitHub.cli, puis gh auth login."
        }
        gh auth status *> $null; Assert-Native "gh auth status (connecte-toi avec gh auth login)"
        git fetch --quiet origin main; Assert-Native "git fetch"
        if ((git rev-parse HEAD) -ne (git rev-parse origin/main)) { throw "main n'est pas synchronisée avec GitHub (git pull / git push)." }
    }
    Write-Host "Version $current -> $Version $(if ($Prerelease) { '(bêta)' } else { '(stable)' })"

    # ------------------------------------------------------------------ 2. Numéro de version
    Step "Numéro de version"
    Set-ProjectVersion $Version

    # ------------------------------------------------------------------ 3. Tests
    if (-not $SkipTests) {
        Step "Tests du moteur (pytest)"
        Push-Location backend
        try { & .\.venv\Scripts\python.exe -m pytest ..\tests -q; Assert-Native "pytest" }
        finally { Pop-Location }
        Step "Tests de l'interface (vitest)"
        npm --prefix frontend run test --silent; Assert-Native "Tests frontend"
    }

    # ------------------------------------------------------------------ 4. Compilation signée
    Step "Compilation signée"
    & (Join-Path $PSScriptRoot "build-release.ps1")

    # ------------------------------------------------------------------ 5. Fichiers de la release
    Step "Préparation de releases\$Tag"
    $bundle = Join-Path $Root "desktop\src-tauri\target\release\bundle\nsis"
    $builtInstaller = Join-Path $bundle "CoC AutoFarm_${Version}_x64-setup.exe"
    if (-not (Test-Path "$builtInstaller.sig")) { throw "Installateur ou signature introuvable : $builtInstaller" }

    $out = Join-Path $Root "releases\$Tag"
    Remove-Item $out -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory $out | Out-Null
    # Nom sans espace : GitHub remplacerait les espaces par des points.
    $installerName = "CoC-AutoFarm_${Version}_x64-setup.exe"
    Copy-Item $builtInstaller (Join-Path $out $installerName)

    $notes = Get-ReleaseNotes $Version
    [IO.File]::WriteAllText((Join-Path $out "notes.md"), $notes, $Utf8)

    $platform = [ordered]@{
        signature = (Get-Content -Raw "$builtInstaller.sig").Trim()
        url       = "https://github.com/$Repo/releases/download/$Tag/$installerName"
    }
    # Structure de base que cette version sait lire : l'application refuse un retour
    # vers une version qui ne pourrait pas ouvrir la base (ex. bêta -> stable).
    $schemaVersion = & (Join-Path $Root "backend\.venv\Scripts\python.exe") -I -c `
        "import sys; sys.path.insert(0, r'$Root\backend'); from app.database.migrations import LATEST_VERSION; print(LATEST_VERSION)"
    Assert-Native "Lecture de la version du schéma"
    $latest = [ordered]@{
        version        = $Version
        notes          = $notes
        pub_date       = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        schema_version = [int] $schemaVersion
        platforms      = [ordered]@{ "windows-x86_64" = $platform; "windows-x86_64-nsis" = $platform }
    }
    [IO.File]::WriteAllText((Join-Path $out "latest.json"), ($latest | ConvertTo-Json -Depth 5), $Utf8)
    $sha256 = (Get-FileHash (Join-Path $out $installerName) -Algorithm SHA256).Hash.ToLower()
    Get-ChildItem $out | Select-Object Name, @{ n = "Taille (Mo)"; e = { [math]::Round($_.Length / 1MB, 2) } } | Format-Table | Out-Host
    Write-Host "SHA-256 de l'installateur : $sha256"

    if ($DryRun) {
        Step "Mode essai : rien n'est publié. Fichiers prêts dans $out"
        return
    }

    # ------------------------------------------------------------------ 6. Publication
    Step "Commit, tag et push"
    git add -- @($Originals.Keys); Assert-Native "git add"
    git commit --quiet -m "Version $Version"; Assert-Native "git commit"
    $Originals.Clear() # commités : ne plus les restaurer
    git tag -a $Tag -m "CoC AutoFarm $Version"; Assert-Native "git tag"
    git push --quiet origin main; Assert-Native "git push"
    git push --quiet origin $Tag; Assert-Native "git push du tag"

    Step "Création de la release GitHub"
    $releaseArgs = @(
        "release", "create", $Tag,
        (Join-Path $out $installerName), (Join-Path $out "latest.json"),
        "--repo", $Repo, "--title", "CoC AutoFarm $Version", "--notes-file", (Join-Path $out "notes.md")
    )
    if ($Prerelease) { $releaseArgs += "--prerelease" }
    gh @releaseArgs
    if ($LASTEXITCODE -ne 0) {
        throw "La release GitHub n'a pas été créée (le tag $Tag est déjà poussé). Relance uniquement : gh $($releaseArgs -join ' ')"
    }

    Step "Canal bêta"
    Update-BetaChannel (Join-Path $out "latest.json") $semver
    Step "Version $Version publiée : https://github.com/$Repo/releases/tag/$Tag"
}
finally {
    # Essai ou échec avant publication : on remet les fichiers de version comme avant.
    Restore-Files
    Pop-Location
}
