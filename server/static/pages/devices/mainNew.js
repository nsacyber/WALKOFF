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
    return $("#deviceForm").serialize();
}

function displayDevices(data){
    for(device in data){
        $("#deviceList").append($('<option>', {device : data[device]["name"]}).text(data[device]["name"]));
    }
}

function displayDeviceForm(data){
    for(param in data){
        if(data[param] != "None"){
            paramVal = data[param];
            if(param == "ip") {
                param = param + "addr";
            }
            $("#deviceForm input[name='" + param + "']").val(paramVal);
        } else {
            if(param == "ip") {
                param = param + "addr";
            }
            $("#deviceForm input[name='" + param + "']").val("");
        }
    }
    $("#deviceForm input[name='pw']").val("");
}

function getDeviceList() {
    $("#deviceList").empty();
    $.ajax({
        'async': false,
        'type': "GET",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "/apps/" + activeApp + "/devices",
        'success': function (data) {
            displayDevices(data);
        },
        'error': function (data){
            $.notify('Error retrieving devices for app ' + activeApp + '.', "error");
            console.log(data);
        }
    });
}

for(var app in apps){
    $("#appList").append($('<option>', {app : apps[app]}).text(apps[app]));
}

$("#appList").on("change", function(data){
    activeApp = data.currentTarget[data.currentTarget.selectedIndex].innerHTML;
    getDeviceList();
});

$("#deviceList").on("change", function(data){
    activeDevice = data.currentTarget[data.currentTarget.selectedIndex].innerHTML;
    $.ajax({
        'async': false,
        'type': "GET",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "/apps/" + activeApp + "/devices/" + activeDevice,
        'success': function (data) {
            displayDeviceForm(data);
        }
    });
});

$("#addNewDevice").on("click", function(){
    formData = addNewDevice();
    if(activeApp){
        $.ajax({
            'async': false,
            'type': "PUT",
            'global': false,
            'data':formData,
            'headers':{"Authentication-Token":authKey},
            'url': "/apps/" + activeApp + "/devices/" + $("#deviceForm #name").val(),
            'success': function (data) {
                $("#deviceForm")[0].reset();
                getDeviceList();
                $.notify('Device successfully added.', "success");
            },
            'error': function(data){
                $.notify('Device could not be added.', "error");
                console.log(data);
            }
        });
    }
});

$("#removeDevice").on("click", function(){
    if(activeApp && activeDevice){
        $.ajax({
            'async': false,
            'type': "DELETE",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/apps/" + activeApp + "/devices/" + activeDevice,
            'success': function (data) {
                $("#deviceForm")[0].reset();
                getDeviceList();
                $.notify('Device ' + activeDevice + ' successfully removed.', "success");
            },
            'error': function(e) {
                $.notify('Device ' + activeDevice + ' could not be removed.', "error");
                console.log(e);
            }
        });
    }
});

$("#editDevice").on("click", function(){
    if(activeApp && activeDevice){
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'data': $("#deviceForm").serialize(),
            'headers':{"Authentication-Token":authKey},
            'url': "/apps/" + activeApp + "/devices/" + activeDevice,
            'success': function (data) {
                $("#deviceForm")[0].reset();
                getDeviceList();
                $.notify('Device ' + activeDevice + ' successfully edited.', "success");
            },
            'error': function(data){
                $.notify('Device ' + activeDevice + ' could not be edited.', "error");
                console.log(data);
            }
        });
    }
});