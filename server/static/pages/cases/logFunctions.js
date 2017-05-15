function getEventLogs(case_name){
    var logs = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "GET",
            'global': false,
            'data':{},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases/" + case_name + "/events",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    return logs;
}

function getCases(){
    var logs = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "GET",
            'global': false,
            'data':{},
            'headers':{"Authentication-Token":authKey},
            'url': "/cases",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    return logs;
}

function formatCaseSelection(data){
    console.log(data.cases);
    for(x in data.cases){
        $("#caseSelect").append("<li class='list-group-item'>" + data.cases[x].name + "</li>");

    }
}

function formatLogData(data){
    var dataSet = [];
    for(prop in data){
        row = [];
        row.push(data[prop].id);
        row.push(data[prop].timestamp);
        row.push(data[prop].type);
        row.push(data[prop].ancestry);
        row.push(data[prop].data);
        row.push(data[prop].message);
        dataSet.push(row);
    }
    return dataSet;
}

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
      body: currentWorkflow + " was executed!",
    });

    notification.onclick = function () {
      window.open("https://github.com/iadgov");
    };

  }
}
