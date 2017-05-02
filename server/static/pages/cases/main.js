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
        }
    });
    return tmp;
}();

var cases = getCases();
formatCaseSelection(cases);

var dataSet = [];

dataTable = $("#logDataTable").DataTable({
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

$("#caseSelect > li").on("click", function(e){
    //Clears the table
    dataTable.clear().draw();

    //Gets the data
    var selectedCase = e.currentTarget.innerText;
    var data = getEventLogs(selectedCase);
    var dataSet = formatLogData(data);

    //Adds the new rows
    dataTable.rows.add(dataSet);
    dataTable.draw();
});