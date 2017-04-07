function formatCasesForJSTree(cases){
    var result = [];
    for(x in cases){
        result.push({"id": cases[x].id, "text": cases[x].name, "type": "case"});
    }
    return result;
}

function resetSubscriptionModal(){
    $("#modalObjectTypeSelection > option").remove();
    $(".objectSelection > option").remove();
    $(".subscriptionSelection").empty()
}

function resetCaseModal(){
    $("#editCaseDialog").empty();
    $("#editCaseDialog").html(defaultCaseModal);
}

function createSubscriptionModal(){
    window.editSubscriptionDialog = defaultSubscriptionDialog.dialog({
                        autoOpen: false,
                        height:600,
                        width:500,
                        open:
                            function(event, ui){
                                for(key in window.availableSubscriptions){
                                    objectTypeSelection.append("<option value='" + key + "'>" + key + "</option>");
                                }
                                selected_objectType = objectTypeSelection.first()[0].value;
                                formatModal(window.availableSubscriptions, selected_objectType);
                        },
                        close: function(event, ui){
                            $(this).dialog("destroy");
                            $("#editSubscriptionDialog").remove();
                            window.editCaseSubscriptionDialog = null;
                        }
                    });
    return editSubscriptionDialog;
}

function formatAncestry(element, fields){
    switch(fields[field]){
        case "controller":
            formatControllerSubscriptions(element, availableSubscriptions[fields[field]]);
        break;
        case "playbook":
            formatPlaybookSubscriptions(element, availableSubscriptions[fields[field]]);
        break;
        case "workflow":
            formatWorkflowSubscriptions(element, availableSubscriptions[fields[field]]);
        break;
        case "step":
            formatStepSubscriptions(element, availableSubscriptions[fields[field]]);
        break;
        case "nextstep":
            formatNextStepSubscriptions(element, availableSubscriptions[fields[field]]);
        break;
        case "flag":
            formatFlagSubscriptions(element, availableSubscriptions[fields[field]]);
        break;
        case "filter":
            formatFilterSubscriptions(element, availableSubscriptions[fields[field]]);
        break;
    }
}


function formatModal(elements, selected_objectType){
    fields = populateObjectSelectionList(elements, selected_objectType);
    var id, element;
    for(field in fields){
        id = "#" + fields[field] +"ObjectSelection";
        element = $(id).get(0);
        formatAncestry(element, fields);
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
                console.log(typeof editCaseSubscriptionDialog);
                if(typeof window.editCaseSubscriptionDialog === 'undefined' || window.editCaseSubscriptionDialog === null){
                    createSubscriptionModal();
                }
                window.editSubscriptionDialog.dialog("open");

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

