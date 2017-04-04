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

