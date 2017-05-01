function formatCasesForJSTree(cases){
    var result = [];
    for(x in cases){
        result.push({"id": cases[x].id, "text": cases[x].name, "type": "case"});
    }
    return result;
}

function addCase(id){
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "PUT",
            'global': false,
            'data':{"format":"cytoscape"},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + id ,
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
            'type': "DELETE",
            'global': false,
            'data':{"format":"cytoscape"},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + id,
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    return status;
}

function editCase(id){

}

function addNewSubscription(selectedCase, subscriptionId){
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "PUT",
            'global': false,
            'data':JSON.stringify({"ancestry":[], "events":[]}),
            'dataType':"application/json",
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + selectedCase + "subscriptions/",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    console.log(status);
    return status;
}

function removeSelectedSubscription(selectedCase){
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "DELETE",
            'global': false,
            'data':{"format":"cytoscape"},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + selectedCase + "subscriptions/",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    stat = {"status": 1}
    return stat;
}

function editSubscription(selectedCase, ancestry, events){
    stat = {"status": 0};
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'data':ancestry,
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + selectedCase + "/subscriptions",
            'success': function (data) {
                tmp = data;
                stat = {"status": 1};
            }
        });
        return tmp;
    }();
    console.log(status);
    $("#ancestryAjaxForm > li").remove();
    return stat;
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

function getCaseDetails(selectedCase){
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "GET",
            'global': false,
            'data':{},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + selectedCase,
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    console.log(status);
    stat = {"status": 1}
    return stat;
}

function getSubscriptionDetails(selectedCase){
    var status = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "GET",
            'global': false,
            'data':{},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + selectedCase + "/subscriptions",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    console.log(status);
    stat = {"status": 1}
    return stat;
}

function displayCaseDetails(subscriptionDetails){
    for(item in subscriptionDetails){

    }
}

function getSelectedObjects(){
    var selectedOptions = objectSelectionDiv.find("select > option").filter(":selected").map(function(){
        return {"type": $(this).data()["type"], "value": this.value};
    }).get();
    return selectedOptions;
}

function getSelectedList(){
    var selectedOptions = [];
    $.each($("#objectSelectionDiv > li:visible > input"), function(i , el){
        var x = $(el).val() || "";
        selectedOptions.push(x);
    });
    return selectedOptions;
}

function getCheckedEvents(){
    var selectedEvents = [];
    $.each($(".subscriptionSelection > li > input:checked"), function(i, el){
        var x = $(el).val() || "";
        selectedEvents.push(x);
    });
    return selectedEvents;
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
    if(index < $(".objectSelection").length){
        $(".objectSelection").slice((index+1), $(".objectSelection").length).parent().hide();
    }

    if(index > 0){
         result = Object.keys(availableSubscriptions).slice(0, index+1 || index);
    }else{
        result = [selected_objectType]
    }
    return result;
}

function formatControllerSubscriptions(element, availableSubscriptions){
    var option;
    for(controller in controllers){
        option = $("<option></option>");
        option.attr("data-type", "controller");
        option.val(controllers[controller]);
        option.text(controllers[controller]);

        $(element).append(option);
    }
}

function formatPlaybookSubscriptions(element, availableSubscriptions){
    var playbooks = Object.keys(loadedWorkflows);
    for(playbook in playbooks){
        var option = $("<option></option>");
        option.attr("data-type", "playbook");
        option.val(playbooks[playbook]);
        option.text(playbooks[playbook]);

        element.append(option);
    }
}

function formatWorkflowSubscriptions(element, availableSubscriptions, previous){
    var workflows = loadedWorkflows[previous[1]];
    for(workflow in workflows){
        element.append("<option data-type='workflow' value='" + workflows[workflow] + "'>" + workflows[workflow] + "</option>");
    }
}

function formatStepSubscriptions(element, availableSubscriptions){
    var steps = getWorkflowElements(playbook, workflow, elements);
    for(workflow in workflows){
        element.append("<option data-type='step' value='" + workflows[workflow] + "'>" + workflows[workflow] + "</option>");
    }
}

function formatNextStepSubscriptions(element, availableSubscriptions){
}

function formatFlagSubscriptions(element, availableSubscriptions){
}

function formatFilterSubscriptions(element, availableSubscriptions){
}
