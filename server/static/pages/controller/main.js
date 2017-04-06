editSubscriptionDialog = $("#editSubscriptionDialog").dialog({
                    autoOpen: false,
                    height:600,
                    width:500,
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
availableSubscriptions = JSON.parse(availableSubscriptions);

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

