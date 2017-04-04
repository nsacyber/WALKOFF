function formatCasesForJSTree(cases){
    var result = [];
    if(cases == null || cases == "" || cases.length == 0){

    }
    return result;
}

function casesCustomMenu(node){
    var items = {
        addSubscription: {
            label: "Add Subscription",
            action: function () {
                var new_case = $("#casesTree").jstree().get_node($("#casesTree").jstree("get_selected").pop());
                var id = new_case.children.length;
                $("#casesTree").jstree("create_node", new_case, 'inside', {"state": "open", "id": id, "text" : "new case " + id, "type":"case"}, false, false);

            }
        },

    };
    if (node.original.type != "case") {
        console.log(node)
        // Delete the "delete" menu item
        delete items.addSubscription;
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
    $("#casesTree").jstree().create_node("#", {"id": id, "text" : "new case " + id, "type":"case"}, "last", function(){});
});