function formatCasesForJSTree(cases){
    var result = [];
    for(x in cases){
        result.push({"id": cases[x].id, "text": cases[x].name, "type": "case"})
    }
    return result;
}

function formatControllerSubscriptions(availableSubscriptions){
    $("#modalObjectSelection").empty();
    console.log(controllers);
    for(controller in controllers){
        $("#modalObjectSelection").append("<option value='" + controllers[controller] + "'>" + controllers[controller] + "</option>");
    }
    for(subscription in availableSubscriptions){
        sub = availableSubscriptions[subscription];
        $("#subscriptionSelection").append("<li><input type='checkbox' name='" + sub + "' value='" + sub + "' /><label for='" + sub + "'>" + sub + "</label></li>")
    }
}

function formatWorkflowSubscriptions(availableSubscriptions){

}

function formatStepSubscriptions(availableSubscriptions){

}

function formatNextStepSubscriptions(availableSubscriptions){

}

function formatFlagSubscriptions(availableSubscriptions){

}

function formatFilterSubscriptions(availableSubscriptions){

}

function resetSubscriptionModal(){
    $("#editSubscriptionDialog").empty();
    $("#editSubscriptionDialog").html(defaultModal);
}

function resetCaseModal(){
    $("#editCaseDialog").empty();
    $("#editCaseDialog").html(defaultCaseModal);
}

function formatModal(availableSubscriptions){
    for(key in availableSubscriptions){
        $("#modalObjectTypeSelection").append("<option value='" + key + "'>" + key + "</option>");
    }
    selected = $("#modalObjectTypeSelection option").first()[0].value;
    console.log(Object.keys(availableSubscriptions).slice(0, Object.keys(availableSubscriptions).indexOf(selected)));
    switch(selected){
        case "controller":
            formatControllerSubscriptions(availableSubscriptions[selected]);
        break;
        case "workflow":
            formatWorkflowSubscriptions(availableSubscriptions);
        break;
        case "step":
            formatStepSubscriptions(availableSubscriptions);
        break;
        case "nextstep":
            formatNextStepSubscriptions(availableSubscriptions);
        break;
        case "flag":
            formatFlagSubscriptions(availableSubscriptions);
        break;
        case "filter":
            formatFilterSubscriptions(availableSubscriptions);
        break;
    }
}

function openEditSubscriptionModal(){
    var availableSubscriptions = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "GET",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/availableSubscriptions",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    availableSubscriptions = JSON.parse(availableSubscriptions);
    resetSubscriptionModal();
    formatModal(availableSubscriptions);
    editSubscriptionDialog.dialog("open");
}

function openEditCaseModal(){
    resetCaseModal();
    editCaseDialog.dialog("open");
}

function casesCustomMenu(node){
    var items = {
        editCase:{
            label: "Edit Case",
            action: function () {
                openEditCaseModal();
            }
        },
        removeCase:{
            label: "Remove Case",
            action: function () {
                var selected_case = $("#casesTree").jstree().get_node($("#casesTree").jstree("get_selected").pop());
                $("#casesTree").jstree().delete_node([selected_case]);
                removeCase(selected_case.text);
            }
        },
        addSubscription: {
            label: "Add Subscription",
            action: function () {
                var selected_case = $("#casesTree").jstree().get_node($("#casesTree").jstree("get_selected").pop());
                console.log(selected_case);
                var id = selected_case.children.length;
                $("#casesTree").jstree("create_node", selected_case,  {"id": "sub_"+id, "text" : "new subscription " + id, "type":"subscription"}, false, false);

            }
        },
        editSubscription: {
            label: "Edit Subscription",
            action: function () {
                openEditSubscriptionModal();
            }
        },

    };
    if (node.original.type != "case") {
        delete items.addSubscription;
        delete items.editCase;
    }
    else if(node.original.type != "subscription"){
        delete items.editSubscription;
    }
    return items;
}

var cases = function () {
    var tmp = null;
    $.ajax({
        'async': false,
        'type': "GET",
        'global': false,
        'data':{"format":"cytoscape"},
        'headers':{"Authentication-Token":authKey},
        'url': "/cases",
        'success': function (data) {
            tmp = data;
            console.log(data);
        }
    });
    return tmp;
}();
cases = JSON.parse(cases);
$("#casesTree").jstree({
    'core':{
        'check_callback': true,
        'data': formatCasesForJSTree(cases.cases)
    },
    'plugins':['contextmenu'],
    'contextmenu':{
        items: casesCustomMenu
    }
});

$("#addCase").on("click", function(){
    id = Object.keys($("#casesTree").jstree()._model.data).length;
    name = "case_"+id;
    $("#casesTree").jstree().create_node("#", {"id": name, "text" : name, "type":"case"}, "last", function(){});
    addCase(name);
});