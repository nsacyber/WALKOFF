defaultSubscriptionDialog = $("#editSubscriptionDialog");

window.editSubscriptionDialog = defaultSubscriptionDialog.dialog({
                    autoOpen: false,
                    height:600,
                    width:500,
                    open:
                        function(event, ui){
//                            for(key in window.availableSubscriptions){
//                                objectTypeSelection.append("<option value='" + key + "'>" + key + "</option>");
//                            }
//                            selected_objectType = objectTypeSelection.first()[0].value;
//                            formatModal(window.availableSubscriptions, selected_objectType);
                    },
                    close: function(event, ui){
                        $(this).dialog("destroy");
                        $("#editSubscriptionDialog").remove();
                        window.editCaseSubscriptionDialog = null;
                    }
                });


editCaseDialog = $("#editCaseDialog").dialog({
                    autoOpen: false,
                    height:400,
                    width:350,
                    modal:true
                });

selected_objectType = null;

objectSelectionDiv = $(document).find("#objectSelectionDiv");
//objectTypeSelection = $(document).find("#modalObjectTypeSelection");

//Keeps track of the current event object
Window.currentSelection = null;

availableSubscriptions = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "GET",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/availablesubscriptions",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
window.availableSubscriptions = availableSubscriptions;

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
    $("#casesTree").jstree().create_node("#", {"id": name, "text" : name, "type":"case", "icon": "jstree-file"}, "last", function(){});
    addCase(name);
});

//$("#modalObjectTypeSelection").on("change", function(){
//    //$(".objectSelection").parent().show();
//    //$(".objectSelection > option").remove();
//    $(".subscriptionSelection").empty();
//    selected_objectType = this.value;
//    formatModal(availableSubscriptions,selected_objectType);
//});


editSubscriptionDialog.on("dialogclose", function(event, ui){
    resetSubscriptionModal();
});

objectSelectionDiv.on("change", '.objectSelection', function(){
    getSelectedObjects();
});

$("#submitForm").on("click", function(){
    var selectedSub = $("#casesTree").jstree().get_node($('#casesTree').jstree().get_selected()).text;
    var selectedCase =  $("#casesTree").jstree().get_node($("#casesTree").jstree().get_parent(selectedSub)).text;
    var ancestryForm = $("#ancestryAjaxForm");
    var inputs = $(".container").find("input").toArray();
    inputs.shift();
    
    $.each(inputs, function(i, e){
        var elem = $("<li></li>");
        elem.append($(e).clone());
        $("#ancestryAjaxForm").append(elem);
    });

    var selectedEvents = getCheckedEvents();
//    $.each(selectedEvents, function(i, e){
//        var elem = $("<li></li>");
//        var eventInput = $("<input type='text'></input>");
//        eventInput.attr("name", "events-" + i);
//        eventInput.attr("value", e);
//        elem.append(eventInput);
//        $("#ancestryAjaxForm").append(elem);
//    });

    var elements = ancestryForm.serializeArray();
    var ancestry = [];
    for(var x in elements){
        ancestry.push(elements[x]["value"]);
    }
    r = editSubscription(selectedSub, ancestry, selectedEvents);
    window.editSubscriptionDialog.dialog("close");
});


//objects = Object.keys(availableSubscriptions);
$('.objectSelectionDiv').each(function() {
    $(this).repeatable_fields({
        wrapper: 'table',
        container: 'tbody',
        is_sortable: false,
        row_count_placeholder:'$rowCount',
        after_add: function(e){
            var index = $(e).children().length-2;
            if(index < 7){
                var type = availableSubscriptions[index] ? availableSubscriptions[index].type : null;
                if(type) {
                    Window.currentSelection = availableSubscriptions[index];
                    $(e).children().eq(index+1).find("td.rowLabel").html(type);
                    $(e).children().eq(index+1).find("input").attr("name", "ancestry-" + index)
                    $(e).children().eq(index+1).find("input").attr("id", "ancestry-" + index)
                }
                $(".subscriptionSelection").empty();
                formatSubscriptionList(availableSubscriptions[index].events);
            }
            else{
                $(e).children().eq(index+1).remove();
            }
        },
        after_remove: function(e){
            var index = $(e).children().length-2;
            if(index <= 7){
                Window.currentSelection = availableSubscriptions[index];
                $(".subscriptionSelection").empty();
                formatSubscriptionList(availableSubscriptions[index].events);
            }
        }
    });
});

//Initialize workflow results datatable
var workflowResultsTable = $("#workflowResultsTable").DataTable({
    columns:[
        { data: "name", title: "Workflow Name" },
        { data: "timestamp", title: "Timestamp" },
        { data: "result", title: "Result" }
    ],
    order: [1, 'desc']
});

//Grab the initial data from the server
var dataSet = function getInitialWorkflowResults(){
    var results = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "GET",
            'global': false,
            'data':{},
            'headers':{"Authentication-Token":authKey},
            'url': "/workflowresults",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    return results;
}();

//Adds the new rows
workflowResultsTable.rows.add(dataSet);
workflowResultsTable.draw();

//Set up event listener for workflow results if possible
if (typeof(EventSource) !== "undefined") {
    var workflowResultsSSE = new EventSource('workflowresults/stream');
    workflowResultsSSE.onmessage = function(message) {
        workflowResultsTable.row.add(JSON.parse(message.data));
        workflowResultsTable.draw();
    }
    workflowResultsSSE.onerror = function(){
        workflowResultsSSE.close();
    }
}
else {
    console.log('EventSource is not supported on your browser. Please switch to a browser that supports EventSource to receive real-time updates.');
}