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
                console.log(data);
            }
        });
        return tmp;
    }();

    return logs;
}

function populateTable(data){

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
