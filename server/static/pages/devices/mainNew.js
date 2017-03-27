var activeApp = undefined;
var activeDevice = undefined;

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
        $("#deviceList").append($('<option>', {device : data[device]["name"]}).text(data[device]["name"]));
    }
}

function displayDeviceForm(data){
    for(param in data){
        if(data[param] != "None"){
            $("#deviceForm input[name='" + param + "']").val(data[param]);
        }
    }
}

for(var app in apps){
    $("#appList").append($('<option>', {app : apps[app]}).text(apps[app]));
}

$("#appList").on("change", function(data){
    var result;
    $("#deviceList").empty();
    activeApp = data.currentTarget[data.currentTarget.selectedIndex].innerHTML;
    if(activeApp != undefined){
         $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/configuration/" + activeApp + "/devices/all",
            'success': function (data) {
                console.log(data);
                var result = JSON.parse(data);
                displayDevices(result);
            },
            'error': function (data){
                console.log('applist failed');
                console.log(data);
            }
        });
    }

});

$("#deviceList").on("change", function(data){
    activeDevice = data.currentTarget[data.currentTarget.selectedIndex].innerHTML;
    $.ajax({
        'async': false,
        'type': "POST",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "/configuration/" + activeApp + "/devices/" + activeDevice + "/display",
        'success': function (data) {
            var result = JSON.parse(data);
            displayDeviceForm(result);
        }
    });
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

$("#removeDevice").on("click", function(){
    if(activeApp && activeDevice){
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/configuration/" + activeApp + "/devices/" + activeDevice + "/remove",
            'success': function (data) {
                console.log(data);
            }
        });
    }

});
$("#editDevice").on("click", function(){
    console.log(activeApp);
    console.log(activeDevice);
    if(activeApp && activeDevice){
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/configuration/" + activeApp + "/devices/" + activeDevice + "/edit",
            'success': function (data) {
                console.log(data);
            },
            'errro':function(data){
                console.log('edit device failed');
                console.log(data);
            }

        });
    }

});