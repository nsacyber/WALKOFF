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
    console.log(status);
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

}

function removeSubscription(selectedCase, subscriptionId){

}