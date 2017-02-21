$("#executeWorkflowButton").on("click", function(e){
    var result = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/workflow/" + currentWorkflow + "/execute",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
    console.log(JSON.parse(result));
    notifyMe();
})

if(currentWorkflow){
    var workflowData = function () {
        var tmp = null;
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/workflow/" + currentWorkflow + "/cytoscape",
            'success': function (data) {
                tmp = data;
            }
        });
        return tmp;
    }();
}

console.log(workflowData);

var cy = cytoscape({
  container: document.getElementById('cy'),
  
  boxSelectionEnabled: false,
  autounselectify: true,
  zoomingEnabled:false,
  style: [
    {
      selector: 'node',
      css: {
        'content': 'data(id)',
        'text-valign': 'center',
        'text-halign': 'center',
        'width':'50',
        'height':'50'
      }
    },
    {
      selector: '$node > node',
      css: {
        'padding-top': '10px',
        'padding-left': '10px',
        'padding-bottom': '10px',
        'padding-right': '10px',
        'text-valign': 'top',
        'text-halign': 'center',
        'background-color': '#bbb'
      }
    },
    {
      selector: 'edge',
      css: {
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
      }
    },
    {
      selector: ':selected',
      css: {
        'background-color': 'black',
        'line-color': 'black',
        'target-arrow-color': 'black',
        'source-arrow-color': 'black'
      }
    }
  ],


});

cy.add(JSON.parse(workflowData));
cy.layout({
    name: 'breadthfirst',
    fit:true,
    padding: 5,
    root:"#start"
 });

cy.$('*').on('click', function(e){
  // This function displays info about a node/edge when clicked upon next to the graph

  function jsonStringifySort(obj) {
      // Sort keys so they are displayed in alphabetical order
      return JSON.stringify(Object.keys(obj).sort().reduce(function (result, key) {
        result[key] = obj[key];
        return result;
    }, {}), null, 2);
  }

  var ele = e.cyTarget;
  var parameters = ele.data().parameters;
  var parametersAsJsonString = jsonStringifySort(parameters);
  $("#parameters").text(parametersAsJsonString);
});

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
