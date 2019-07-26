param([string]$mode)

$valid_modes = "init", "build", "push", "up", "status", "stop", "down"

$help = @'

Usage: walkoff.ps1 {mode}

Valid modes:

init    Create requisite artifacts for Walkoff (e.g. pgdata volume, encryption key, etc.)
build   Builds all needed components in walkoff-stack-windows.yml
up      Deploys the Walkoff stack
stop    Removes the Walkoff stack
down    Removes artifacts created for Walkoff by init
'@

function init {
    # Create volume for persisting workflows, globals, server config, etc.
    # Regular bind mounts do not work on Windows for Postgres due to permissions issues.
    Write-Host -NoNewline "Creating walkoff_default network: "
    docker network create --attachable --driver overlay walkoff_default

    Write-Host -NoNewline "Creating local volume for persisting Postgres data: "
    docker volume create --name walkoff_pgdata -d local

    # Create encryption key for encrypting globals, server data.
    Write-Host -NoNewline "Creating secret key for encrypting Walkoff data: "
    docker run --rm python:3.7.4-slim-buster python -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)))" | docker secret create walkoff_encryption_key -

    if (-Not (Test-Path '.\data\portainer' -PathType Container)) {
        Write-Host "Creating directory for persisting Portainer data: "
        New-Item -Path '.\data\portainer' -ItemType Directory | Out-Null
    }

    if (-Not (Test-Path '.\data\registry' -PathType Container)) {
        Write-Host "Creating directory for persisting Registry data: "
        New-Item -Path '.\data\registry' -ItemType Directory | Out-Null
    }
}

function build {
    # Temporarily bring up registry so we can write to it
    docker-compose -f "walkoff-stack-windows.yml" --log-level ERROR up -d resource_registry

    Write-Host "Beginning build process."

    # Build and push app_sdk first as it is a dependency for all other apps
    docker-compose -f "walkoff-stack-windows.yml" --log-level ERROR build app_sdk
    docker-compose -f "walkoff-stack-windows.yml" --log-level ERROR push app_sdk

    # Build and push everything else
    docker-compose -f "walkoff-stack-windows.yml" --log-level ERROR build
    docker-compose -f "walkoff-stack-windows.yml" --log-level ERROR push

    # Take down the registry until it's needed in up (CRITICAL suppresses walkoff_network not found as it's never created here)
    docker-compose -f "walkoff-stack-windows.yml" --log-level CRITICAL down
}

function up {
    Write-Host "Deploying Walkoff stack..."
    docker stack deploy --compose-file walkoff-stack-windows.yml walkoff

    Write-Host "Some services may take some time to be ready. Use .\walkoff.ps1 status to check on them."
}

function status {

    while(1) {
        $r = docker stack services walkoff | % {$_ -replace '\s{2,}', ','}
        cls
        Write-Host "Watching WALKOFF services (Ctrl+C to quit):"
        $r | ConvertFrom-Csv | Sort-Object -Property Name | Format-Table
        sleep 1
    }
}

function stop {
    Write-Host "Removing Walkoff stack..."
    docker stack rm walkoff
}

function down {
    Write-Host -NoNewline "Removing local volume walkoff_pgdata: "
    docker volume rm walkoff_pgdata

    Write-Host -NoNewline "Removing secret walkoff_encryption_key: "
    docker secret rm walkoff_encryption_key

    Write-Host "Removing contents of .\data\registry"
    Remove-Item -recurse ".\data\registry\*"

    Write-Host "Removing contents of .\data\portainer"
    Remove-Item -recurse ".\data\portainer\*"

    Write-Host "Some services may take some time to stop."
}

if ($valid_modes | Where-Object {$mode -like $_}) {
    Invoke-Expression $mode
} else {
    Write-Host $help
}
