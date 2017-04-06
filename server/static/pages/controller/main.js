editSubscriptionDialog = $("#editSubscriptionDialog").dialog({
                    autoOpen: false,
                    height:400,
                    width:350,
                    modal:true
                });

defaultModal = $("#editSubscriptionDialog").html();

editCaseDialog = $("#editCaseDialog").dialog({
                    autoOpen: false,
                    height:400,
                    width:350,
                    modal:true
                });

defaultCaseModal = $("#editCaseDialog").html();

selected_objectType = null;

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

var status = function () {
    var tmp = null;
    $.ajax({
        'async': false,
        'type': "GET",
        'global': false,
        'data':{"ancestry":{"ancestry":["start"]}},
        'headers':{"Authentication-Token":authKey},
        'url': "/playbook/test/helloWorldWorkflow/display",
        'dataType':"json",
        'success': function (data) {
            tmp = data;
            console.log(data);
        }
    });
    return tmp;
}();