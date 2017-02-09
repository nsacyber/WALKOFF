$(document).ready(function(){
    //Menu and dropdown buttons
    $("#ss_installApp").on("click", function(e){
        $.ajax({
            url:'/installApp/',
            data:{"system":"true", "app": "installApp", "page": "index", "args":'{"action":"install"}'},
            type:"POST",
            success: function(e){
                data = JSON.parse(e);
                $("#ss_main").html(data["content"]);
            },
            error: function(e){
                $("#ss_main").html("<p> Interface could not be Loaded! </p>");
            }
        });
    });

    $("#ss_help").on("click", function(e){
        $.ajax({
            url:'/help/',
            data:{"system":"true", "app": "help", "page": "index", "args":'{"action":"display"}'},
            type:"POST",
            success: function(e){
                data = JSON.parse(e);
                $("#ss_main").html(data["content"]);
            },
            error: function(e){
                $("#ss_main").html("<p> Interface could not be Loaded! </p>");
            }
        });
    });

    $("#ss_userSettings").on("click", function(e){
        console.log("user settings");
    });

    $("#ss_userLogout").on("click", function(e){
        console.log("logging out");
    });

    $("#ss_playbook").on("click", function(e){
        console.log("playbook clicked");
        $.ajax({
            url:'interface/playbook/display',
            data:{},
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success: function(e){
                data = e;
                $("#ss_main").html(data);
            },
            error: function(e){
                $("#ss_main").html("<p> Interface could not be Loaded! </p>");
            }
        });
    });

    $("#ss_devices").on("click", function(e){
        $.ajax({
            url:'/interface/devices/display',
            data:{},
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success: function(e){
                data = e;
                $("#ss_main").html(data);
            },
            error: function(e){
                $("#ss_main").html("<p> Interface could not be Loaded! </p>");
            }
        });
    });

    $("#ss_settings").on("click", function(e){
        $.ajax({
            url:'/interface/settings/display',
            headers:{"Authentication-Token":authKey},
            data:{},
            type:"POST",
            success: function(e){
                data = e;
                $("#ss_main").html(data);
            },
            error: function(e){
                $("#ss_main").html("<p> Interface could not be Loaded! </p>");
            }
        });
    });

    $("#ss_triggers").on("click", function(e){
        $.ajax({
            url:'/interface/triggers/display',
            data:{},
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success: function(e){
                data = e;
                $("#ss_main").html(data);
            },
            error: function(e){
                $("#ss_main").html("<p> Interface could not be Loaded! </p>");
            }
        });
    });

    $(".installedApp").on("click", function(e){
        app = e["target"]["childNodes"][1]["data"].trim()
        $.ajax({
            url:'/apps/' + app + '/display',
            data:{"page": "index.html", "key-0":"name", "value-0":"testing"},
			headers:{"Authentication-Token":authKey},
            type:"POST",
            success: function(e){
                data = e;
                $("#ss_main").html(e);
                $("#main").resize();
            },
            error: function(e){
                $("#ss_main").html("<p> Interface could not be Loaded! </p>");
            }
        });
    });
})