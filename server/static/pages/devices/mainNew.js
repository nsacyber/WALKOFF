function displayNameList(devices){
    for(device in devices){
        if(devices[device]["name"] != undefined){
            $("#deviceList").append($('<option>', {device:devices[device]}).text(device[devices]));
        }
    }
}

for(var app in apps){
    $("#appList").append($('<option>', {app : apps[app]}).text(apps[app]));
}

$("#appList").on("change", function(data){
    var result;
    console.log(data);
    $.ajax({
        'async': false,
        'type': "POST",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "/configuration/" + data.value + "/devices",
        'success': function (data) {
            console.log(data);
        }
    });
});