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
                console.log("ERRROR");
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
                console.log("ERRROR");
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
            url:'/shortstopPlaybook/',
            data:{"system":"true", "app": "playbook", "page": "index", "args":'{"action":"display"}'},
            type:"POST",
            success: function(e){
                data = JSON.parse(e);
                $("#ss_main").html(data["content"]);
            },
            error: function(e){
                console.log("ERRROR");
            }
        });
    });

    $("#ss_settings").on("click", function(e){
        console.log("shortstop settings");
        $.ajax({
            url:'/shortstopSettings/',
            data:{"system":"true", "app": "systemSettings", "page": "settings", "args":'{"action":"read"}'},
            type:"POST",
            success: function(e){
                data = JSON.parse(e);
                $("#ss_main").html(data["content"]);
            },
            error: function(e){
                console.log("ERRROR");
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
				console.log(e);
                data = e;
                $("#ss_main").html(e);
            },
            error: function(e){
                console.log("ERRROR");
            }
        });
    });
})