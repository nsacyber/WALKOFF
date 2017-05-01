var cases = function () {
    var tmp = null;
    $.ajax({
        'async': false,
        'type': "GET",
        'global': false,
        'data':{"format":"cytoscape"},
        'headers':{"Authentication-Token":authKey},
        'url': "/cases/subscriptions",
        'success': function (data) {
            tmp = data;
            console.log(data);
        }
    });
    return tmp;
}();

var data = getEventLogs("case_2");
populateTable(data);