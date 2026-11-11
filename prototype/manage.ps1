param(
    [Parameter(Position=0)]
    [ValidateSet('prepare','check','up','status','seed','test','backup','restore-check','down')]
    [string]$Action = 'status'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$runtimeDir = Join-Path $projectRoot '.runtime'
$envFile = Join-Path $runtimeDir 'prototype.env'
$composeFile = Join-Path $PSScriptRoot 'compose.yml'

function Prepare-Environment {
    New-Item -ItemType Directory -Force $runtimeDir | Out-Null
    if (-not (Test-Path -LiteralPath $envFile)) {
        $lines = foreach ($name in @('DB_ROOT_PASSWORD','ADMIN_PASSWORD','AV_SALES_PASSWORD','AV_PM_PASSWORD')) {
            $secret = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
            "$name=$secret"
        }
        [IO.File]::WriteAllLines($envFile, $lines, [Text.UTF8Encoding]::new($false))
    }
    Write-Output 'Local prototype settings prepared. Existing passwords preserved.'
}

function Find-Docker {
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($candidate in @(
        'C:\Program Files\Docker\Docker\resources\bin\docker.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe')
    )) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    throw 'Docker is not installed. Install and start Docker Desktop with Linux containers.'
}

function Compose {
    & $script:dockerExe compose --project-name av-prototype --env-file $envFile -f $composeFile @args
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed (exit $LASTEXITCODE)." }
}

if ($Action -eq 'prepare') { Prepare-Environment; return }
$dockerExe = Find-Docker
if (-not (Test-Path -LiteralPath $envFile)) { Prepare-Environment }
if ($Action -eq 'check') {
    & $dockerExe --version
    & $dockerExe compose version
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose is unavailable.' }
    Compose config --quiet
    $containerOS = & $dockerExe info --format '{{.OSType}}'
    if ($LASTEXITCODE -ne 0) { throw 'Docker engine is unavailable. Start Docker Desktop; restart Windows if installation requires it.' }
    if ($containerOS -ne 'linux') { throw 'Switch Docker Desktop to Linux containers.' }
    Write-Output 'Docker engine is ready for Linux containers.'
    return
}
if ($Action -eq 'up') {
    Compose up -d --build --wait --wait-timeout 600
    Compose exec -T backend bench version --format json
    Write-Output 'Prototype: http://localhost:8080. Credentials are in .runtime/prototype.env.'
}
if ($Action -eq 'status') { Compose ps -a }
if ($Action -eq 'seed') {
    try {
        foreach ($line in Get-Content -LiteralPath $envFile) {
            $name, $value = $line.Split('=', 2)
            if ($name -in @('AV_SALES_PASSWORD', 'AV_PM_PASSWORD')) {
                [Environment]::SetEnvironmentVariable($name, $value, 'Process')
            }
        }
        Compose exec -T -e AV_SALES_PASSWORD -e AV_PM_PASSWORD backend bench --site av.localhost execute av_platform.demo.seed
    } finally {
        Remove-Item Env:AV_SALES_PASSWORD,Env:AV_PM_PASSWORD -ErrorAction SilentlyContinue
    }
}
if ($Action -eq 'test') {
    Compose exec -T backend bench --site av.localhost run-tests --app av_platform --skip-test-records
}
if ($Action -eq 'backup') {
    Compose exec -T backend bench --site av.localhost backup --with-files
    $target = Join-Path $runtimeDir ('backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Force $target | Out-Null
    Compose cp 'backend:/home/frappe/frappe-bench/sites/av.localhost/private/backups/.' $target
    Write-Output "Backup files copied to $target. Restore is a separate check."
}
if ($Action -eq 'restore-check') {
    try {
        foreach ($line in Get-Content -LiteralPath $envFile) {
            $name, $value = $line.Split('=', 2)
            if ($name -eq 'DB_ROOT_PASSWORD') {
                [Environment]::SetEnvironmentVariable($name, $value, 'Process')
            }
        }
        Compose exec -T -e DB_ROOT_PASSWORD backend ./env/bin/python /opt/av-prototype/restore_check.py
    } finally {
        Remove-Item Env:DB_ROOT_PASSWORD -ErrorAction SilentlyContinue
    }
}
if ($Action -eq 'down') {
    Compose down  # Keep all volumes, backups and source files.
}
