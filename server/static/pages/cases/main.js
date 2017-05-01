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

var data = getEventLogs("case_1");
var dataSet = formatLogData(data);

$("#logDataTable").DataTable({
    data: dataSet,
    columns:[
     {title: "id"},
     {title: "timestamp"},
     {title: "type"},
     {title: "ancestry"},
     {title: "data"},
     {title: "message"}
    ]
});