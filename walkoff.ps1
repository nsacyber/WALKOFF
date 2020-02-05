$ErrorActionPreference = "Stop";

$BUILDARG="^-[a-zA-Z]*b|--build"
if ($args[0] -eq "up") {
    foreach ($arg in $args) {
        if ($arg -match $BUILDARG) {
            Write-Host "Preparing WALKOFF Bootloader..."
            docker build -t walkoff_bootloader -f bootloader/Dockerfile .
            break
        }
    }
}

Write-Host "Starting WALKOFF Bootloader..."

try {
    docker network inspect walkoff_network 2>$null
} catch {
    Write-Host -NoNewLine "Creating walkoff_network network: "
    docker network create --attachable=True --driver=overlay walkoff_network
}

$unixified_wd = "/" + $(Get-Location | Select-Object -ExpandProperty Path | %{ $_ -replace "\\", "/" -replace ":", ""} | %{$_.ToLower().Trim("/")} )

docker run --rm -it --network walkoff_network --name walkoff_bootloader `
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock `
    --mount type=bind,source=$unixified_wd,target=$unixified_wd `
    --mount type=bind,source=$unixified_wd/data/config.yml,target=/common_env.yml `
    -e DOCKER_HOST=unix:///var/run/docker.sock `
    -w $unixified_wd `
    walkoff_bootloader $args

$CLEANARG="^-[a-zA-Z]*c|--clean"
if ($args[0] -eq "down") {
    foreach ($arg in $args) {
        if ($arg -match $CLEANARG) {
            Write-Host -NoNewLine "Removing walkoff_network network: "
            docker network rm walkoff_network
            break
        }
    }
}
