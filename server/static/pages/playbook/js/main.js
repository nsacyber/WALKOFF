$("#executeWorkflowButton").on("click", function(e){
    notifyMe();
})


var workflowData = function () {
    var tmp = null;
    $.ajax({
        'async': false,
        'type': "POST",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "/workflow/multiactionWorkflow/cytoscape",
        'success': function (data) {
            tmp = data;
        }
    });
    return tmp;
}();

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
        'text-halign': 'center'
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
        'curve-style': 'bezier'
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
  
  layout: {
    name: 'preset',
    padding: 5
  }
});

cy.add(JSON.parse(workflowData));
cy.center(cy.elements());