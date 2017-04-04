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


$("#executeWorkflowButton").on("click", function(e){
    var result = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'data':{"format":"cytoscape"},
            'headers':{"Authentication-Token":authKey},
            'url': "/workflow/" + currentWorkflow + "/execute",
            'success': function (data) {
                console.log(data);
                tmp = data;
            }
        });
        return tmp;
    }();
    console.log(result.output);

    cy.add(result);
    cy.layout({
        name: 'breadthfirst',
        fit:true,
        padding: 5,
        root:"#start"
     });
    notifyMe();
})

$("#innerSidebar").accordion({
        collapsible: true,
        active: 'none',
        heightStyle: 'fill'
    }
);

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
