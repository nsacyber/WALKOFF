function formatPlaybooksForJSTree(playbook_data){
    var result = [];
    var x = 1;
    for(playbook in playbook_data){
        entry = {"id":x.toString(), "text":playbook, "type":"playbook"};
        var workflows = [];
        for(workflow in playbook_data[playbook]){
            x++;
            workflows.push({"id":x.toString(), "text":playbook_data[playbook][workflow], "type":"workflow"})
        }
        entry["children"] = workflows;
        result.push(entry);
        x++;
    }
    return result;
}

function executeWorkflow(currentPlaybook, currentWorkflow){
    var result = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "playbooks/" + currentPlaybook + "/workflows/" + currentWorkflow + "/execute",
            'success': function (data) {
                tmp = data;
                $("#eventList").append("<li>" + currentWorkflow + " is executing </li>");
            }
        });
        return tmp;
    }();
    if(result.status == "success"){
        $("#eventList").append("<li>" + currentWorkflow + " executed successfully </li>");
    }
    notifyMe();
}

function customMenu(node){
    var items = {
        executeItem: {
            label: "Execute Workflow",
            action: function () {
                var playbook = $("#loadedPlaybooksTree").jstree(true).get_node(node.parents.shift()).text;
                var workflow = node.text;
                executeWorkflow(playbook, workflow);
            }
        },
        addCase: {
            label: "Add Case",
            action: function () {
                var playbook = $("#loadedPlaybooksTree").jstree(true).get_node(node.parents.shift()).text;
                addCaseDialog.dialog("open");

            }
        },

    };
    if (node.original.type != "workflow") {
        delete items.executeItem;
        delete items.addCase;
    }

    return items;
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