param (
    [string]$appname = $(throw "-appname is required"),
    [string]$appversion = $(throw "-appversion is required"),
    [switch]$updatesdk = $true,
    [switch]$updateapp = $true
)

$sdkname = "app_sdk_v2"
$sdktag = "127.0.0.1:5000/walkoff_" + $sdkname 

If ($updatesdk) {
    docker build -t $sdktag -f $sdkname/Dockerfile . 
    docker push $sdktag
    docker service update --force walkoff_$sdkname 
}
If ($updateapp){
    $app_dir = "apps/" + $appname + "/" + $appversion
    $full_app_name = "walkoff_app_" + $appname

    $app_tag = "127.0.0.1:5000/" + $full_app_name + ":" + $appversion

    docker build -f $app_dir/Dockerfile -t $app_tag $app_dir 
    docker push $app_tag
    docker service update --force $full_app_name
}
