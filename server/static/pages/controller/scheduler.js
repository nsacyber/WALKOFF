$("#status").text(schedulerStatus(schedulerStatusNo));

$("#startSchedulerBtn").on("click", function(e){
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
        return JSON.parse(tmp);
    }();
    console.log(result);
    $("#status").text(schedulerStatus(result["status"]));
});

$("#pauseSchedulerBtn").on("click", function(e){
    var result = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/execution/scheduler/pause",
            'success': function (data) {
                tmp = data;
            }
        });
        return JSON.parse(tmp);
    }();
    $("#status").text(schedulerStatus(result["status"]));
});

$("#stopSchedulerBtn").on("click", function(e){
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
        return JSON.parse(tmp);
    }();

    $("#status").text(schedulerStatus(result["status"]));
});