<#
.SYNOPSIS
    Builds a Windows portable distribution of the Datavisor application.

.DESCRIPTION
    Creates a self-contained folder that bundles an embeddable CPython runtime,
    all Python dependencies, the built Vue SPA, and small launcher scripts.
    After building, the user can zip the folder and share it; the recipient
    only needs to extract and double-click Start.bat — no Python installation
    on the target machine is required.

.PARAMETER OutputDir
    Destination folder. Will be wiped if -Force is supplied.

.PARAMETER PythonVersion
    Embeddable CPython version to download from python.org.

.PARAMETER Force
    Allow overwriting an existing OutputDir.

.PARAMETER SkipPythonDownload
    Reuse a previously cached embeddable zip in TEMP.

.PARAMETER SmokeTest
    After building, launch the package and probe /health, then stop.

.EXAMPLE
    .\Dev\Build-Portable.ps1 -Force
    .\Dev\Build-Portable.ps1 -Force -SmokeTest
#>
[CmdletBinding()]
param(
    [string]$OutputDir = 'D:\VS\Portable\Datavisor-Portable',
    [string]$PythonVersion = '3.11.9',
    [switch]$Force,
    [switch]$SkipPythonDownload,
    [switch]$SmokeTest
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'  # speeds up Invoke-WebRequest

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
$RepoRoot     = Split-Path -Parent $PSScriptRoot
$PythonZipUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$GetPipUrl    = 'https://bootstrap.pypa.io/get-pip.py'
$EmbedZip     = Join-Path $env:TEMP "python-$PythonVersion-embed-amd64.zip"

# Runtime dependencies — keep in sync with pyproject.toml [project.dependencies]
$RuntimeDeps = @(
    'polars>=1.0.0',
    'duckdb>=1.0.0',
    'pydantic[email]>=2.0.0',
    'pyarrow>=15.0.0',
    'openpyxl>=3.1.0',
    'pyyaml>=6.0.0',
    'python-dateutil>=2.8.0',
    'fastapi>=0.115.0',
    'uvicorn[standard]>=0.30.0',
    'python-multipart>=0.0.9',
    'sqlalchemy>=2.0.0',
    'alembic>=1.13.0',
    'aiosqlite>=0.20.0',
    'python-jose[cryptography]>=3.3.0',
    'bcrypt>=4.0.0',
    'reportlab>=4.0.0',
    'matplotlib>=3.8.0',
    'jinja2>=3.0.0'
)
# Note: asyncpg is intentionally omitted — portable uses SQLite only.

function Write-Step($Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Robocopy {
    param([string]$Src, [string]$Dst, [string[]]$ExtraArgs = @())
    $args = @($Src, $Dst, '/MIR', '/NFL', '/NDL', '/NJH', '/NJS', '/NP') + $ExtraArgs
    & robocopy @args | Out-Null
    # robocopy: exit codes 0..7 are success, >=8 is failure
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed ($LASTEXITCODE): $Src -> $Dst"
    }
    $global:LASTEXITCODE = 0
}

# ---------------------------------------------------------------------------
# 1. Pre-flight + cleanup
# ---------------------------------------------------------------------------
Write-Step "Pre-flight checks"

if (-not (Test-Path "$RepoRoot\api\main.py")) {
    throw "Unexpected layout: $RepoRoot\api\main.py not found. Run from repo root."
}
if (-not (Test-Path "$RepoRoot\frontend\dist\index.html")) {
    throw "frontend\dist\index.html missing. Build the SPA first: cd frontend; npm run build"
}

if (Test-Path $OutputDir) {
    if (-not $Force) {
        throw "Output exists: $OutputDir. Pass -Force to overwrite."
    }
    Write-Step "Removing existing $OutputDir"
    Remove-Item $OutputDir -Recurse -Force
}

# ---------------------------------------------------------------------------
# 2. Create folder structure
# ---------------------------------------------------------------------------
Write-Step "Creating folder structure"
$Dirs = @(
    $OutputDir,
    "$OutputDir\runtime\python",
    "$OutputDir\app",
    "$OutputDir\data\datasets",
    "$OutputDir\data\uploads",
    "$OutputDir\logs"
)
$Dirs | ForEach-Object { New-Item -ItemType Directory -Path $_ -Force | Out-Null }

# ---------------------------------------------------------------------------
# 3. Download embeddable Python
# ---------------------------------------------------------------------------
if ((-not (Test-Path $EmbedZip)) -or (-not $SkipPythonDownload)) {
    Write-Step "Downloading $PythonZipUrl"
    Invoke-WebRequest -Uri $PythonZipUrl -OutFile $EmbedZip
} else {
    Write-Step "Using cached embeddable Python: $EmbedZip"
}
Write-Step "Extracting embeddable Python"
Expand-Archive -Path $EmbedZip -DestinationPath "$OutputDir\runtime\python" -Force

# ---------------------------------------------------------------------------
# 4. Enable site-packages in embeddable runtime
# ---------------------------------------------------------------------------
Write-Step "Enabling site-packages and app path in ._pth"
$PthFile = Get-ChildItem "$OutputDir\runtime\python\python*._pth" | Select-Object -First 1
if (-not $PthFile) { throw "._pth file not found in embeddable distribution" }
$pth = Get-Content $PthFile.FullName
$pth = $pth -replace '^\s*#\s*import site', 'import site'
# Add app/ to sys.path so `python -m api.seed` and `uvicorn api.main:app` resolve.
# Path is relative to python.exe directory (runtime\python\), so up two levels to portable
# root and then into app.
if (-not ($pth -match [regex]::Escape('..\..\app'))) {
    $pth = @($pth[0]) + '..\..\app' + ($pth[1..($pth.Count - 1)])
}
$pth | Set-Content $PthFile.FullName -Encoding ascii

$PythonExe = Join-Path $OutputDir 'runtime\python\python.exe'

# ---------------------------------------------------------------------------
# 5. Bootstrap pip
# ---------------------------------------------------------------------------
Write-Step "Bootstrapping pip"
$GetPipScript = Join-Path $OutputDir 'runtime\python\get-pip.py'
Invoke-WebRequest -Uri $GetPipUrl -OutFile $GetPipScript
& $PythonExe $GetPipScript --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw "get-pip.py failed with exit code $LASTEXITCODE" }

# ---------------------------------------------------------------------------
# 6. Install runtime dependencies
# ---------------------------------------------------------------------------
Write-Step "Installing $($RuntimeDeps.Count) runtime dependencies (this may take a few minutes)"
& $PythonExe -m pip install --no-warn-script-location --no-cache-dir @RuntimeDeps
if ($LASTEXITCODE -ne 0) { throw "pip install failed with exit code $LASTEXITCODE" }

# ---------------------------------------------------------------------------
# 7. Copy application code
# ---------------------------------------------------------------------------
Write-Step "Copying application code (api, src, frontend/dist)"
Invoke-Robocopy "$RepoRoot\api"            "$OutputDir\app\api"             @('/XD','__pycache__','/XF','*.pyc')
Invoke-Robocopy "$RepoRoot\src"            "$OutputDir\app\src"             @('/XD','__pycache__','/XF','*.pyc')
Invoke-Robocopy "$RepoRoot\frontend\dist"  "$OutputDir\app\frontend\dist"

Copy-Item "$RepoRoot\pyproject.toml"   "$OutputDir\app\" -Force
Copy-Item "$RepoRoot\requirements.txt" "$OutputDir\app\" -Force
if (Test-Path "$RepoRoot\README.md") {
    Copy-Item "$RepoRoot\README.md" "$OutputDir\app\" -Force
}

# ---------------------------------------------------------------------------
# 8. Generate launcher and docs
# ---------------------------------------------------------------------------
Write-Step "Generating Start.bat, Stop.bat, README-PORTABLE.md"

$StartBat = @'
@echo off
setlocal
cd /d "%~dp0"

set "PYTHONHOME=%~dp0runtime\python"
set "PYTHONPATH=%~dp0app;%~dp0runtime\python\Lib\site-packages"
set "PATH=%PYTHONHOME%;%PATH%"

set "DATAVISOR_ROOT=%~dp0"
set "DATABASE_URL=sqlite+aiosqlite:///%~dp0datavisor.db"
set "DATABASE_URL=%DATABASE_URL:\=/%"
set "UPLOAD_DIR=%~dp0data\uploads"
set "FRONTEND_URL=http://localhost:8000"
set "SECRET_KEY=portable-local-only-change-if-shared-externally-32"

if not exist "logs" mkdir logs
if not exist "data\datasets" mkdir data\datasets
if not exist "data\uploads"  mkdir data\uploads

REM First-run: create empty DB and seed predefined carriers + default admin
if not exist "datavisor.db" (
    echo Pierwszy start - inicjalizacja bazy i seed carriers...
    cd app
    "%PYTHONHOME%\python.exe" -m api.seed admin@local.app admin Admin
    cd ..
)

REM Port 8000 free?
netstat -ano | findstr :8000 | findstr LISTENING >nul
if not errorlevel 1 (
    echo.
    echo [BLAD] Port 8000 jest zajety. Zatrzymaj inna aplikacje i sprobuj ponownie.
    echo.
    pause
    exit /b 1
)

echo Uruchamianie serwera...
powershell -NoProfile -Command "$p = Start-Process -FilePath '%PYTHONHOME%\python.exe' -ArgumentList '-m','uvicorn','api.main:app','--host','127.0.0.1','--port','8000' -RedirectStandardOutput '%~dp0logs\server.log' -RedirectStandardError '%~dp0logs\server.err' -PassThru -WindowStyle Hidden -WorkingDirectory '%~dp0app'; $p.Id | Out-File -Encoding ascii '%~dp0logs\server.pid'"

REM Wait for /health (up to ~15 s)
set /a tries=0
:waitloop
set /a tries+=1
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try { (Invoke-WebRequest http://localhost:8000/health -UseBasicParsing -TimeoutSec 1).StatusCode } catch { 0 }" > "%TEMP%\datavisor_health.txt"
set /p health=<"%TEMP%\datavisor_health.txt"
del "%TEMP%\datavisor_health.txt" 2>nul
if "%health%"=="200" goto ready
if %tries% LSS 15 goto waitloop

echo.
echo [BLAD] Serwer nie wystartowal w 15 sekund. Sprawdz logs\server.err
pause
exit /b 1

:ready
start "" http://localhost:8000
echo.
echo ====================================================
echo  Datavisor uruchomiony: http://localhost:8000
echo  Login:  admin@local.app
echo  Haslo:  admin
echo ====================================================
echo.
echo Aby zatrzymac - uruchom Stop.bat (lub zamknij to okno).
pause
'@

$StopBat = @'
@echo off
cd /d "%~dp0"
if exist logs\server.pid (
    powershell -NoProfile -Command "try { Stop-Process -Id (Get-Content logs\server.pid) -Force -ErrorAction Stop; Write-Host 'Zatrzymano Datavisor.' } catch { Write-Host 'Proces juz nie istnieje.' }"
    del logs\server.pid 2>nul
) else (
    echo Brak pliku PID - serwer prawdopodobnie nie dziala.
)
pause
'@

$Readme = @'
# Datavisor — wersja Portable (Windows)

## Jak uruchomic

1. Rozpakuj ZIP w dowolnej lokalizacji (np. `C:\Datavisor`).
   Sciezka NIE moze zawierac polskich znakow ani spacji, jesli to mozliwe.
2. Kliknij dwukrotnie **Start.bat**.
3. Po chwili otworzy sie przegladarka pod adresem http://localhost:8000.
4. Zaloguj sie:
   - Login: `admin@local.app`
   - Haslo: `admin`

## Jak zatrzymac

- Kliknij **Stop.bat**, lub
- Zamknij okno terminala uruchomione przez Start.bat.

## Gdzie sa moje dane

Wszystko zostaje w folderze obok Start.bat:
- `datavisor.db` — baza (uzytkownicy, ruchy, konfiguracje)
- `data\uploads\` — wgrane pliki (masterdata, orders)
- `data\datasets\` — datasety DuckDB
- `logs\server.log` / `server.err` — logi serwera

Przeniesienie calego folderu = przeniesienie aplikacji ze wszystkimi danymi.
Aplikacja **nic nie zostawia** w rejestrze Windows ani w `%APPDATA%`.

## Problemy?

- **Port 8000 zajety** — Start.bat pokaze blad. Zamknij aplikacje uzywajaca portu.
- **Antywirus blokuje python.exe** — dodaj folder do wyjatkow.
- **Pierwszy start trwa dluzej** — to normalne, tworzona jest baza i seed carriers.
- **Aplikacja nie startuje** — zajrzyj do `logs\server.err`.

## Co tu jest

- `runtime\python\` — wbudowany Python 3.11 (niezalezny od systemu)
- `app\` — kod aplikacji (FastAPI + zbudowany frontend Vue)
- `data\` — Twoje dane
- `logs\` — logi

Aplikacja dziala w pelni lokalnie. Brak polaczen sieciowych poza localhost.
'@

Set-Content -Path "$OutputDir\Start.bat"          -Value $StartBat -Encoding ascii
Set-Content -Path "$OutputDir\Stop.bat"           -Value $StopBat  -Encoding ascii
Set-Content -Path "$OutputDir\README-PORTABLE.md" -Value $Readme   -Encoding utf8

# ---------------------------------------------------------------------------
# 9. Validate package
# ---------------------------------------------------------------------------
Write-Step "Validating package"

$Stowaways = @()
$Stowaways += Get-ChildItem $OutputDir -Recurse -Include '*.pyc'           -Force -ErrorAction SilentlyContinue
$Stowaways += Get-ChildItem $OutputDir -Recurse -Include '__pycache__'     -Force -Directory -ErrorAction SilentlyContinue
$Stowaways += Get-ChildItem $OutputDir -Recurse -Include 'datavisor.db'    -Force -ErrorAction SilentlyContinue
$Stowaways += Get-ChildItem $OutputDir -Recurse -Include '.env'            -Force -ErrorAction SilentlyContinue
$Stowaways += Get-ChildItem $OutputDir -Recurse -Include 'node_modules'    -Force -Directory -ErrorAction SilentlyContinue
if ($Stowaways.Count -gt 0) {
    Write-Warning "Found unexpected files (will be left in place — review):"
    $Stowaways | ForEach-Object { Write-Warning "  $($_.FullName)" }
}

$Size = [math]::Round((Get-ChildItem $OutputDir -Recurse -Force | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host ""
Write-Host "Package built: $OutputDir ($Size MB)" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 10. Optional smoke test
# ---------------------------------------------------------------------------
if ($SmokeTest) {
    Write-Step "Smoke test: launching Start.bat..."
    $startProc = Start-Process -FilePath "$OutputDir\Start.bat" -WindowStyle Minimized -PassThru
    try {
        $ok = $false
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 1
            try {
                $r = Invoke-WebRequest 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 1
                if ($r.StatusCode -eq 200) { $ok = $true; break }
            } catch {}
        }
        if ($ok) {
            Write-Host "Smoke test PASSED — /health returned 200." -ForegroundColor Green
        } else {
            Write-Warning "Smoke test FAILED — /health did not respond. Check logs\server.err"
        }
    } finally {
        # Stop the server using the PID file written by Start.bat
        if (Test-Path "$OutputDir\logs\server.pid") {
            $pidValue = Get-Content "$OutputDir\logs\server.pid"
            try { Stop-Process -Id $pidValue -Force -ErrorAction Stop } catch {}
            Remove-Item "$OutputDir\logs\server.pid" -Force -ErrorAction SilentlyContinue
        }
        # Close the Start.bat console window
        try { Stop-Process -Id $startProc.Id -Force -ErrorAction Stop } catch {}

        # Reset to pristine: remove seeded DB and any datasets so the recipient starts clean
        Remove-Item "$OutputDir\datavisor.db" -Force -ErrorAction SilentlyContinue
        Get-ChildItem "$OutputDir\data\datasets" -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem "$OutputDir\logs"          -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "Done. Next steps:"
Write-Host "  1. (Optional) Test manually: cd '$OutputDir'; .\Start.bat"
Write-Host "  2. Zip and share:"
Write-Host "     Compress-Archive '$OutputDir' 'D:\VS\Portable\Datavisor-Portable-v0.1.0.zip' -Force"
