var activeApp = undefined;

function displayNameList(devices){
    for(device in devices){
        if(devices[device]["name"] != undefined){
            $("#deviceList").append($('<option>', {device:devices[device]}).text(device[devices]));
        }
    }
}

function addNewDevice(){
    if($("#name").val() == ""){
        $("#name").val(activeApp + "_newDevice");
    }
    return $("#name").serialize();
}

function displayDevices(data){
    for(device in data){
        console.log(data[device]);
        $("#deviceList").append($('<option>', {device : data[device]["name"]}).text(data[device]["name"]));
    }
}

for(var app in apps){
    $("#appList").append($('<option>', {app : apps[app]}).text(apps[app]));
}

$("#appList").on("change", function(data){
    var result;

    activeApp = data.currentTarget[data.currentTarget.selectedIndex].innerHTML;
    if(activeApp != undefined){
         $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/configuration/" + activeApp + "/devices",
            'success': function (data) {
                var result = JSON.parse(data);
                displayDevices(result);
            }
        });
    }

});

$("#addNewDevice").on("click", function(){
    formData = addNewDevice();
    if(activeApp){
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'data':formData,
            'headers':{"Authentication-Token":authKey},
            'url': "/configuration/" + activeApp + "/devices/add",
            'success': function (data) {
                console.log(data);
            }
        });
    }

});