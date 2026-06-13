[CmdletBinding()]
param(
    [string]$InstallRoot = "",
    [string]$Repository = "dikmri/xMosaic",
    [string]$Tag = "latest",
    [switch]$SkipSystemDependencyInstall
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if (-not $InstallRoot) {
    $InstallRoot = if ($env:XMOSAIC_INSTALL_ROOT) {
        $env:XMOSAIC_INSTALL_ROOT
    }
    else {
        Join-Path $env:LOCALAPPDATA "xMosaic"
    }
}
if ($env:XMOSAIC_INSTALL_TAG) {
    $Tag = $env:XMOSAIC_INSTALL_TAG
}

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Update-ProcessPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = @($machinePath, $userPath) -join ";"
}

function Get-PythonCommand {
    if ($env:XMOSAIC_PYTHON -and (Test-Path -LiteralPath $env:XMOSAIC_PYTHON)) {
        return @($env:XMOSAIC_PYTHON)
    }
    if (Test-Command "python") {
        & python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @("python")
        }
    }
    if (Test-Command "py") {
        & py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @("py", "-3")
        }
    }
    return @()
}

function Invoke-Python {
    param([string[]]$Arguments)
    if ($script:PythonCommand.Count -eq 0) {
        throw "Python 3.11 or later was not found."
    }
    $exe = $script:PythonCommand[0]
    $prefixArgs = @()
    if ($script:PythonCommand.Count -gt 1) {
        $prefixArgs = $script:PythonCommand[1..($script:PythonCommand.Count - 1)]
    }
    & $exe @prefixArgs @Arguments
}

function Ensure-Python {
    $script:PythonCommand = @(Get-PythonCommand)
    if ($script:PythonCommand.Count -gt 0) {
        return
    }
    if ($SkipSystemDependencyInstall -or -not (Test-Command "winget")) {
        throw "Python 3.11 or later is required. Install Python and run this script again."
    }

    Write-Step "Installing Python 3.12 with winget"
    winget install --id Python.Python.3.12 --exact --source winget --scope user --accept-package-agreements --accept-source-agreements --disable-interactivity
    Update-ProcessPath
    $script:PythonCommand = @(Get-PythonCommand)
    if ($script:PythonCommand.Count -eq 0) {
        throw "Python was installed, but this shell cannot find it yet. Open a new PowerShell window and run the installer command again."
    }
}

function Ensure-FFmpeg {
    if ((Test-Command "ffmpeg") -and (Test-Command "ffprobe")) {
        return
    }
    if ($SkipSystemDependencyInstall -or -not (Test-Command "winget")) {
        Write-Warning "FFmpeg/FFprobe was not found. Install FFmpeg before processing videos."
        return
    }

    Write-Step "Installing FFmpeg with winget"
    winget install --id Gyan.FFmpeg.Essentials --exact --source winget --scope user --accept-package-agreements --accept-source-agreements --disable-interactivity
    Update-ProcessPath
    if (-not ((Test-Command "ffmpeg") -and (Test-Command "ffprobe"))) {
        Write-Warning "FFmpeg was installed, but this shell cannot find it yet. Open a new PowerShell window before processing videos."
    }
}

function Get-Release {
    $api = if ($Tag -eq "latest") {
        "https://api.github.com/repos/$Repository/releases/latest"
    }
    else {
        "https://api.github.com/repos/$Repository/releases/tags/$Tag"
    }
    return Invoke-RestMethod -Uri $api -Headers @{ "User-Agent" = "xMosaic-installer" }
}

function Get-Asset {
    param(
        [object]$Release,
        [string]$Pattern
    )
    $asset = $Release.assets | Where-Object { $_.name -like $Pattern } | Select-Object -First 1
    if (-not $asset) {
        throw "Release asset not found: $Pattern"
    }
    return $asset
}

New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ("xmosaic-install-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

try {
    Ensure-Python
    Ensure-FFmpeg

    Write-Step "Resolving xMosaic release"
    $release = Get-Release
    $setupAsset = Get-Asset -Release $release -Pattern "stable-win-x64-xMosaic-Setup.zip"
    $wheelAsset = Get-Asset -Release $release -Pattern "xmosaic-*-py3-none-any.whl"

    $setupZip = Join-Path $tempRoot $setupAsset.name
    $wheelPath = Join-Path $tempRoot $wheelAsset.name

    Write-Step "Downloading desktop installer"
    Invoke-WebRequest -Uri $setupAsset.browser_download_url -OutFile $setupZip -Headers @{ "User-Agent" = "xMosaic-installer" }

    Write-Step "Downloading Python worker"
    Invoke-WebRequest -Uri $wheelAsset.browser_download_url -OutFile $wheelPath -Headers @{ "User-Agent" = "xMosaic-installer" }

    $venvPath = Join-Path $InstallRoot "python"
    if (-not (Test-Path -LiteralPath (Join-Path $venvPath "Scripts\python.exe"))) {
        Write-Step "Creating Python environment"
        Invoke-Python -Arguments @("-m", "venv", $venvPath)
    }

    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    Write-Step "Installing Python worker package"
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install --upgrade $wheelPath
    [Environment]::SetEnvironmentVariable("XMOSAIC_PYTHON", $venvPython, "User")
    $env:XMOSAIC_PYTHON = $venvPython

    $extractPath = Join-Path $tempRoot "desktop"
    Expand-Archive -LiteralPath $setupZip -DestinationPath $extractPath -Force
    $setupExe = Get-ChildItem -LiteralPath $extractPath -Filter "xMosaic-Setup.exe" -Recurse | Select-Object -First 1
    if (-not $setupExe) {
        throw "xMosaic-Setup.exe was not found in the installer archive."
    }

    Write-Step "Running xMosaic desktop installer"
    $process = Start-Process -FilePath $setupExe.FullName -WorkingDirectory $setupExe.DirectoryName -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "xMosaic installer failed with exit code $($process.ExitCode)."
    }

    Write-Step "Installation complete"
    Write-Host "Launch xMosaic from the Start menu."
    Write-Host "Python worker: $venvPython"
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}
