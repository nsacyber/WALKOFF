function formatPlaybooksForJSTree(data){
    var result = [];
    var x = 1;
    for(playbook in data){
        entry = {"id":x.toString(), "text":playbook};
        var workflows = [];
        for(workflow in data[playbook]){
            x++;
            workflows.push({"id":x.toString(), "text":data[playbook][workflow]})
        }
        entry["children"] = workflows;
        result.push(entry);
        x++;
    }
    return result;
}

function notifyMe() {
    if (!Notification) {
        console.log('Desktop notifications not available in your browser. Try Chromium.');
        return;
    }

    if (Notification.permission !== "granted")
        Notification.requestPermission();
    else {
        var notification = new Notification('WALKOFF event', {
            icon: 'http://cdn.sstatic.net/stackexchange/img/logos/so/so-icon.png',
            body: "workflow was executed!",
        });

        notification.onclick = function () {
            window.open("https://github.com/iadgov");
        };

    }
}

function executeWorkflow(currentPlaybook, currentWorkflow){
    var result = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook/" +currentPlaybook + "/" + currentWorkflow + "/execute",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    console.log(JSON.parse(result));
    notifyMe();
}

function customMenu(node){
    var items = {
        executeItem: { // The "rename" menu item
            label: "Execute Workflow",
            action: function () {
                var playbook = $("#loadedPlaybooksTree").jstree(true).get_node(node.parents.shift()).text;
                var workflow = node.text;
                executeWorkflow(playbook, workflow);
            }
        },

    };
    if (node.children.length > 0) {
        // Delete the "delete" menu item
        delete items.executeItem;
    }

    return items;
}

function schedulerStatus(status){
    console.log(status);
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

$("#loadedPlaybooksTree").jstree({
    'core':{
        'data': formatPlaybooksForJSTree(loadedWorkflows)
    },
    'plugins':['contextmenu'],
    'contextmenu':{
        items: customMenu
    }
});

$("#loadedPlaybooksTree").on('loaded.jstree', function(){
    $("#loadedPlaybooksTree").jstree("open_all");
});

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