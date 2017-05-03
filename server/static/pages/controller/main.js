defaultSubscriptionDialog = $("#editSubscriptionDialog");
window.editSubscriptionDialog =
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
window.availableSubscriptions = JSON.parse(availableSubscriptions);

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
    $.each(selectedEvents, function(i, e){
        var elem = $("<li></li>");
        var eventInput = $("<input type='text'></input>");
        eventInput.attr("name", "events-" + i);
        eventInput.attr("value", e);
        elem.append(eventInput);
        $("#ancestryAjaxForm").append(elem);
    });

    r = editSubscription(selectedSub, ancestryForm.serialize(), selectedEvents);
    window.editSubscriptionDialog.dialog("close");
});


objects = Object.keys(availableSubscriptions);
$('.objectSelectionDiv').each(function() {
    jQuery(this).repeatable_fields({
        wrapper: 'table',
        container: 'tbody',
        is_sortable: false,
        row_count_placeholder:'$rowCount',
        after_add: function(e){
            var index = $(e).children().length-2;
            if(index < 7){
                var key = objects[index];
                if(typeof key !== "undefined"){
                    Window.currentSelection = objects[index];
                    $(e).children().eq(index+1).find("td.rowLabel").html(key);
                    $(e).children().eq(index+1).find("input").attr("name", "ancestry-" + index)
                    $(e).children().eq(index+1).find("input").attr("id", "ancestry-" + (index))
                }
                $(".subscriptionSelection").empty();
                formatSubscriptionList(availableSubscriptions[Window.currentSelection]);
            }
            else{
                $(e).children().eq(index+1).remove();
            }
        },
        after_remove: function(e){
            var index = $(e).children().length-2;
            if(index <= 7){
                Window.currentSelection = objects[index];
                $(".subscriptionSelection").empty();
                formatSubscriptionList(availableSubscriptions[Window.currentSelection]);
            }
        }
    });
});