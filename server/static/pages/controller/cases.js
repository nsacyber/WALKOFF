function formatCasesForJSTree(cases){
    var result = [];
    for(x in cases){
        result.push({"id": cases[x].id, "text": cases[x].name, "type": "case"})
    }
    return result;
}

function resetSubscriptionModal(){
    $("select[name=modalObjectTypeSelection]").empty();
    $("#objectSelectionDiv").empty();
    $(".subscriptionSelection").empty()
}

function resetCaseModal(){
    $("#editCaseDialog").empty();
    $("#editCaseDialog").html(defaultCaseModal);
}

function resetObjectSelection(){
    $("#objectSelectionDiv").empty();
}

function formatModal(availableSubscriptions, selected_objectType){
    fields = populateObjectSelectionList(availableSubscriptions, selected_objectType);
    for(field in fields){
        switch(fields[field]){
            case "controller":
                formatControllerSubscriptions(availableSubscriptions[fields[field]]);
            break;
            case "playbook":
                formatPlaybookSubscriptions(availableSubscriptions[fields[field]]);
            break;
            case "workflow":
                formatWorkflowSubscriptions(availableSubscriptions[fields[field]]);
            break;
            case "step":
                formatStepSubscriptions(availableSubscriptions[fields[field]]);
            break;
            case "nextstep":
                formatNextStepSubscriptions(availableSubscriptions[fields[field]]);
            break;
            case "flag":
                formatFlagSubscriptions(availableSubscriptions[fields[field]]);
            break;
            case "filter":
                formatFilterSubscriptions(availableSubscriptions[fields[field]]);
            break;
        }
    }
    formatSubscriptionList(availableSubscriptions[selected_objectType]);
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
                var id = selected_case.children.length;
                $("#casesTree").jstree("create_node", selected_case,  {"id": "sub_"+id, "text" : "new subscription " + id, "type":"subscription"}, false, false);

            }
        },
        editSubscription: {
            label: "Edit Subscription",
            action: function () {
                for(key in availableSubscriptions){
                    $("select[name=modalObjectTypeSelection]").append("<option value='" + key + "'>" + key + "</option>");
                }
                editSubscriptionDialog.dialog("open");
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

$("select[name=modalObjectTypeSelection]").on("change", function(){
    $("#objectSelectionDiv").empty();
    $(".subscriptionSelection").empty();
    selected_objectType = this.value;
    formatModal(availableSubscriptions,selected_objectType);
});

editSubscriptionDialog.on("dialogopen", function(event, ui){
    selected_objectType = $("select[name=modalObjectTypeSelection] option").first()[0].value;
    formatModal(availableSubscriptions, selected_objectType);
    getSelectedObjects();
});

editSubscriptionDialog.on("dialogclose", function(event, ui){
    resetSubscriptionModal();
});

$("#objectSelectionDiv").on("change", '.objectSelection', function(){
    getSelectedObjects();
});

