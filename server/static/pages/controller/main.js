defaultSubscriptionDialog = $("#editSubscriptionDialog");
window.editSubscriptionDialog =
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


editCaseDialog = $("#editCaseDialog").dialog({
                    autoOpen: false,
                    height:400,
                    width:350,
                    modal:true
                });

selected_objectType = null;

objectSelectionDiv = $(document).find("#objectSelectionDiv");
objectTypeSelection = $(document).find("#modalObjectTypeSelection");

availableSubscriptions = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "GET",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/availablesubscriptions",
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

$("#modalObjectTypeSelection").on("change", function(){
    $(".objectSelection").parent().show();
    $(".objectSelection > option").remove();
    $(".subscriptionSelection").empty();
    selected_objectType = this.value;
    formatModal(availableSubscriptions,selected_objectType);
});

//$(".objectSelection").on("change", function(e){
//    var i = $(e.currentTarget).parent().index() + 2;
//    var nextup = $("#objectSelectionDiv > li:nth-child(" + i + ") > select");
//    if(nextup.length){
//        if(nextup.data("type") != "none"){
//            var previous = [];
//            $.each($(e.currentTarget).parent().prevAll(), function(index, value){
//                console.log(value)
//            });
//            formatAncestry(nextup, nextup.data("type"));
//        }
//    }
//})

editSubscriptionDialog.on("dialogclose", function(event, ui){
    resetSubscriptionModal();
});

objectSelectionDiv.on("change", '.objectSelection', function(){
    getSelectedObjects();
});

$("#submitForm").on("click", function(){
    var selectedSub = $('#casesTree').jstree().get_selected();
    var selectedCase =  "case_" + $("#casesTree").jstree().get_parent(selectedSub);

    var selectedObjects = getSelectedList();

    if(selectedObjects.length >= 3){
        selectedObjects[0] = selectedObjects[1] + "-" + selectedObjects[2];
        selectedObjects.splice(2, 1);
    }
    var selectedEvents = getCheckedEvents();

    r = editSubscription(selectedCase, selectedObjects, selectedEvents);
    console.log(r);
    window.editSubscriptionDialog.dialog("close");
});