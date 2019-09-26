param (
    [string]$servicename = $(throw "-servicename is required"),
    [string]$serviceprefix = $(throw "-serviceprefix is required")
)

$fullname = "walkoff_" + $serviceprefix + "_" + $servicename
$servicetag = "127.0.0.1:5000/" + $servicename

docker build -t $servicetag -f $servicename/Dockerfile . 
docker push $servicetag
docker service update --force $fullname