echo "Preparing Walkoff Bootloader..."
docker build -t walkoff_bootloader -f bootloader/Dockerfile .

echo "Creating walkoff_default network..."
docker network create --attachable=True --driver=overlay walkoff_default

echo "Running bootloader..."
# Ip Address from Docker NAT
$ip = $(docker network inspect bridge --format "{{json .IPAM.Config}}" | ConvertFrom-JSON | %{$_.Gateway})

# Working Directory + data\config
$dc = "/" + $(Get-Location | Select-Object -ExpandProperty Path | %{ $_ -replace "\\", "/" -replace ":", ""} | %{$_.ToLower().Trim("/")} ) + "/data/config.yml"

# Working Directory
$wd = "/" + $(Get-Location | Select-Object -ExpandProperty Path | %{ $_ -replace "\\", "/" -replace ":", ""} | %{$_.ToLower().Trim("/")} )

docker run --rm -it --network walkoff_default --name walkoff_bootloader `
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock `
    --mount type=bind,source=$wd,target=$wd `
    --mount type=bind,source=$dc,target=/common_env.yml `
    -e DOCKER_HOST=unix:///var/run/docker.sock `
    -e DOCKER_HOST_IP=$ip `
    --workdir=$wd `
    walkoff_bootloader $args