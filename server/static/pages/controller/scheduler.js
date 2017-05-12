function schedulerStatus(status){
    if(status == 0){
        return "stopped";
    }
    if(status == 2){
        return "paused";
    }
    if(status == 1){
        return "running";
    }
    return "error";
}

$("#status").text(schedulerStatus(schedulerStatusNo));

$("#startSchedulerBtn").on("click", function(e){
    $("#messageDetail").empty();
    var result = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/execution/scheduler/start",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    message = schedulerStatus(result["status"]);
    if(message == "error"){
        $("#messageDetail").text(result["status"]);
    }
    $("#status").text(message);
});

$("#pauseSchedulerBtn").on("click", function(e){
    $("#messageDetail").empty();
    action = $(this).text().toLowerCase();
    console.log(action);
    var result = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/execution/scheduler/" + action,
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    console.log(result);
    message = schedulerStatus(result["status"]);
    if(message == "error"){
        $("#messageDetail").text(result["status"]);
    }
    else{
        if(action == "pause"){
            $(this).text("Resume");
        }else{
            $(this).text("Pause");
        }
    }
    $("#status").text(message);
});

$("#stopSchedulerBtn").on("click", function(e){
    $("#messageDetail").empty();
    var result = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/execution/scheduler/stop",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    message = schedulerStatus(result["status"]);
    if(message == "error"){
        $("#messageDetail").text(result["status"]);
    }
    else{
        $("#pauseSchedulerBtn").text("Pause");
    }
    $("#status").text(message);
});