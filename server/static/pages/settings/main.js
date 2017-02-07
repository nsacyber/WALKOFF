$.ajax({
    url:'configuration/templatePath',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#templatePath").val(data["templatePath"]);
    },
    error: function(e){
        $("#templatePath").val("Error");
    }
});
$.ajax({
    url:'configuration/profileVisualizationsPath',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#profileVisualizationsPath").val(data["profileVisualizationsPath"]);
    },
    error: function(e){
        $("#profileVisualizationsPath").val("Error");
    }
});
$.ajax({
    url:'configuration/keywordsPath',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#keywordsPath").val(data["keywordsPath"]);
    },
    error: function(e){
        $("#keywordsPath").val("Error");
    }
});
$.ajax({
    url:'configuration/dbPath',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#dbPath").val(data["dbPath"]);
    },
    error: function(e){
        $("#dbPath").val("Error");
    }
});

$.ajax({
    url:'configuration/TLS_version',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#TLS_version").val(data["TLS_version"]);
    },
    error: function(e){
        $("#TLS_version").val("Error");
    }
});
$.ajax({
    url:'configuration/certificatePath',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#certificatePath").val(data["certificatePath"]);
    },
    error: function(e){
        $("#certificatePath").val("Error");
    }
});
$.ajax({
    url:'configuration/https',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#https").val(data["https"]);
    },
    error: function(e){
        $("#https").val("Error");
    }
});
$.ajax({
    url:'configuration/privateKeyPath',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#privateKeyPath").val(data["privateKeyPath"]);
    },
    error: function(e){
        $("#privateKeyPath").val("Error");
    }
});

$.ajax({
    url:'configuration/debug',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#debug").val(data["debug"]);
    },
    error: function(e){
        $("#debug").val("Error");
    }
});
$.ajax({
    url:'configuration/defaultServer',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#defaultServer").val(data["defaultServer"]);
    },
    error: function(e){
        $("#defaultServer").val("Error");
    }
});
$.ajax({
    url:'configuration/host',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#host").val(data["host"]);
    },
    error: function(e){
        $("#host").val("Error");
    }
});
$.ajax({
    url:'configuration/port',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#port").val(data["port"]);
    },
    error: function(e){
        $("#port").val("Error");
    }
});