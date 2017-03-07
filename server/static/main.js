$(document).ready(function(){
    //Menu and dropdown buttons
//    $("#ss_installApp").on("click", function(e){
//        $.ajax({
//            url:'/installApp/',
//            data:{"system":"true", "app": "installApp", "page": "index", "args":'{"action":"install"}'},
//            type:"POST",
//            success: function(e){
//                core.stop();
//                data = JSON.parse(e);
//                $("#ss_main").html(data["content"]);
//            },
//            error: function(e){
//                $("#ss_main").html("<p> Interface could not be Loaded! </p>");
//            }
//        });
//    });

//    $("#ss_help").on("click", function(e){
//        $.ajax({
//            url:'/help/',
//            data:{"system":"true", "app": "help", "page": "index", "args":'{"action":"display"}'},
//            type:"POST",
//            success: function(e){
//                data = JSON.parse(e);
//                $("#ss_main").html(data["content"]);
//            },
//            error: function(e){
//                $("#ss_main").html("<p> Interface could not be Loaded! </p>");
//            }
//        });
//    });

    $("#ss_userSettings").on("click", function(e){
        console.log("user settings");
    });

    $("#ss_userLogout").on("click", function(e){
        console.log("logging out");
    });

    $("#ss_playbook").on("click", function(e){
        core.stop();
        core.start("systemPage", {
            options: {page: "playbook"}
        });
    });

    $("#ss_devices").on("click", function(e){
        core.stop();
        core.start("systemPage", {
            options: {page: "devices"}
        });
    });

    $("#ss_settings").on("click", function(e){
        core.stop();
        core.start("systemPage", {
            options: {page: "settings"}
        });
    });

    $("#ss_triggers").on("click", function(e){
        core.stop();
        core.start("systemPage", {
            options: {page: "triggers"}
        });
    });

    $("#ss_cases").on("click", function(e){
        core.stop();
        core.start("systemPage", {
            options: {page: "cases"}
        });
    });

    $("#ss_debug").on("click", function(e){
        core.stop();
        core.start("systemPage", {
            options: {page: "debug"}
        });
    });

    $(".installedApp").on("click", function(e){
        app = e["target"]["childNodes"][1]["data"].trim()
        core.stop();
        core.start("systemPage", {
            options: {
                preface:"apps",
                page:app,
                data:{"page": "index.html", "key-0":"name", "value-0":"testing"},
            }
        });
    });
})