function addCase(id){
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'data':{"format":"cytoscape"},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + id + "/add",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    return status;
}

function removeCase(id){
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'data':{"format":"cytoscape"},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + id + "/delete",
            'success': function (data) {
                tmp = data;
                console.log(data);
            }
        });
        return tmp;
    }();
    return status;
}

function editCase(id){

}

function addSubscription(selectedCase, subscriptionId){
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'data':{"format":"cytoscape"},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/subscriptions/" + selectedCase + "/subscription/add",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    return status;
}

function removeSubscription(selectedCase, subscriptionId){
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'data':{"format":"cytoscape"},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/subscriptions/" + selectedCase + "/subscription/add",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    return status;
}

function getWorkflowElements(playbook, workflow, elements){
    var url = "/playbook/" + playbook + "/" + workflow + "/display";
    //var ancestry = {"ancestry":{"ancestry":["start"]}};
    var ancestry = {"ancestry":elements};
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "GET",
            'global': false,
            'data':ancestry,
            'headers':{"Authentication-Token":authKey},
            'url': url,
            'dataType':"json",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    return status;
}

function getSelectedObjects(){
    var selectedOptions = $("#objectSelectionDiv").find("select > option").filter(":selected").map(function(){
        return {"type": $(this).data()["type"], "value": this.value};
    }).get();
    console.log(selectedOptions);
    return selectedOptions;
}

function formatSubscriptionList(availableSubscriptions){
    for(subscription in availableSubscriptions){
        sub = availableSubscriptions[subscription];
        $(".subscriptionSelection").append("<li><input type='checkbox' name='" + sub + "' value='" + sub + "' /><label for='" + sub + "'>" + sub + "</label></li>");
    }
}

function populateObjectSelectionList(availableSubscriptions, selected_objectType){
    var index = Object.keys(availableSubscriptions).indexOf(selected_objectType);
    var result;
    if(index > 0){
         result = Object.keys(availableSubscriptions).slice(0, index);
    }else{
        result = [selected_objectType]
    }
    return result;
}

function formatControllerSubscriptions(availableSubscriptions, elements){
    $("#objectSelectionDiv").append("<li><label for='controllerObjectSelection'>Controller</label><select name='controllerObjectSelection' class='objectSelection'></select></li>");
    for(controller in controllers){
        $("select[name=controllerObjectSelection]").append("<option data-type='controller' value='" + controllers[controller] + "'>" + controllers[controller] + "</option>");
    }

}

function formatPlaybookSubscriptions(availableSubscriptions, elements){
    $("#objectSelectionDiv").append("<li><label for='playbookObjectSelection'>Playbook</label><select name='playbookObjectSelection' class='objectSelection'></select></li>");
    var playbooks = Object.keys(loadedWorkflows);
    for(playbook in playbooks){
        $("select[name=playbookObjectSelection]").append("<option data-type='playbook' value='" + playbooks[playbook] + "'>" + playbooks[playbook] + "</option>");
    }
}

function formatWorkflowSubscriptions(availableSubscriptions, elements){
    $("#objectSelectionDiv").append("<li><label for='workflowObjectSelection'>Workflow</label><select name='workflowObjectSelection' class='objectSelection'></select></li>");
    var workflows = loadedWorkflows[playbook];
    for(workflow in workflows){
        $("select[name=workflowObjectSelection]").append("<option data-type='workflow' value='" + workflows[workflow] + "'>" + workflows[workflow] + "</option>");
    }
}

function formatStepSubscriptions(availableSubscriptions, elements){
    $("#objectSelectionDiv").append("<li><label for='stepObjectSelection'>Step</label><select name='stepObjectSelection' class='objectSelection'></select></li>");

    var steps = getWorkflowElements(playbook, workflow, elements);
    for(workflow in workflows){
        $("select[name=workflowObjectSelection]").append("<option data-type='step' value='" + workflows[workflow] + "'>" + workflows[workflow] + "</option>");
    }
}

function formatNextStepSubscriptions(availableSubscriptions, elements){
    $("#objectSelectionDiv").append("<li><label for='nextStepObjectSelection'>Next Step</label><select name='nextStepObjectSelection' class='objectSelection'></select></li>");
}

function formatFlagSubscriptions(availableSubscriptions, elements){
    $("#objectSelectionDiv").append("<li><label for='flagObjectSelection'>Flag</label><select name='flagObjectSelection' class='objectSelection'></select></li>");
}

function formatFilterSubscriptions(availableSubscriptions, elements){
    $("#objectSelectionDiv").append("<li><label for='filterObjectSelection'>Filter</label><select name='filterObjectSelection' class='objectSelection'></select></li>");
}
