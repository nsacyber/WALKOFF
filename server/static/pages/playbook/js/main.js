$(function(){
    "use strict";

    //--------------------
    // Top level variables
    //--------------------

    var currentWorkflow = null;
    var cy = null;
    var ur = null;

    //--------------------
    // Top level functions
    //--------------------

    // Reformat the JSON data returned from the /apps/actions endpoint
    // into a format that jsTree can understand.
    function formatAppsActionJsonDataForJsTree(data) {
        data = JSON.parse(data);
        var jstreeData = [];
        $.each(data, function( key, value ) {
            var appName = key;
            var actionNames = data[key];
            var app = {};
            app.text = key;
            app.children = [];
            for (var i=0; i<actionNames.length; ++i) {
                app.children.push({text: actionNames[i], icon: "jstree-file", data: {app: appName}});
            }
            jstreeData.push(app);
        });
        return jstreeData;
    }


    // Reformat the JSON data returned from the /workflows endpoint
    // into a format that jsTree can understand.
    function formatWorkflowJsonDataForJsTree(data) {
        data = JSON.parse(data).workflows.sort();
        var jstreeData = [];
        $.each(data, function( index, value ) {
            var workflowName = value;
            var app = {};
            app.text = workflowName;
            app.icon = "jstree-file";
            jstreeData.push(app);
        });
        return jstreeData;
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


    function onClickNew(e) {
        var ele = e.cyTarget;
        var parameters = ele.data().parameters;
        var data = [
            {
                text: "Id: " + ele.data().id
            },
            {
                text: "Name: " + parameters.name
            },
            {
                text: "Action: " + parameters.app + "/" + parameters.action
            },
            {
                text: "Device: " + parameters.device
            },
            {
                text: "Input: " + JSON.stringify(parameters.input)
            },
            {
                text: "Errors: " + JSON.stringify(parameters.errors)
            },

        ];
        $('#parameters').jstree({
            'core' : {
                "animation" : 0,
                'force_text' : true,
                'data' : data,
                "check_callback" : true
            },
            "plugins" : [ "wholerow", "state", "types", "contextmenu" ]
        });
    }


    // This function displays info about a node/edge when clicked upon next to the graph
    function onClick(e) {

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
    }


    // This is called while the user is dragging
    function dragHelper( event ) {
        // Return empty div for helper so that original dragged item does not move
        return '<div></div>';
    }


    // This function is called when the user drops a new node onto the graph
    function handleDropEvent( event, ui ) {
        if (cy === null)
            return;

        var draggable = ui.draggable;
        var draggableId   = draggable.attr('id');
        var draggableNode = $('#actions').jstree(true).get_node(draggableId);
        var app = draggableNode.data.app;
        var action = draggableNode.text;

        // The following coordinates is where the user dropped relative to the
        // top-left of the graph
        var x = event.pageX - this.offsetLeft;
        var y = event.pageY - this.offsetTop;

        // Find next available id
        var id = 1;
        while (true) {
            var element = cy.getElementById(id.toString());
            if (element.length === 0)
                break;
            id += 1;
        }

        // Add the node with the id just found to the graph in the location dropped
        // into by the mouse.
        var newNode = ur.do('add', {
            group: 'nodes',
            data: {
                id: id.toString(),
                label: action,
                parameters: {
                    action: action,
                    app: app,
                    device: "None",
                    errors: [
                        {
                            name: "None",
                            nextStep: "None",
                            flags: []
                        }
                    ],
                    input: {},
                    name: action,
                    next: [
                        {
                            name: "None",
                            nextStep: "None",
                            flags: []
                        }
                    ],
                }
            },
            renderedPosition: { x: x, y: y }
        });

        newNode.on('click', onClick);
    }


    // This function removes selected nodes and edges
    function removeSelectedNodes() {
        var selecteds = cy.$(":selected");
        if (selecteds.length > 0)
            ur.do("remove", selecteds);
    }


    function cut() {
        var selecteds = cy.$(":selected");
        if (selecteds.length > 0) {
            cy.clipboard().copy(selecteds);
            ur.do("remove", selecteds);
        }
    }


    function copy() {
        cy.clipboard().copy(cy.$(":selected"));
    }


    function paste() {
        var newNodes = ur.do("paste");
        newNodes.on('click', onClick);
    }


    function newWorkflow(workflowName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/workflow/" + workflowName + "/add",
            'success': function (data) {
                loadWorkflow("Workflow1");
            }
        });
    }


    function saveWorkflow(workflowName) {
        if (cy) {
            var workflowData = JSON.stringify({filename: "", cytoscape: JSON.stringify(cy.elements().jsons())});
            $.ajax({
                'async': false,
                'type': "POST",
                'global': false,
                'dataType': 'json',
                'contentType': 'application/json; charset=utf-8',
                'headers':{"Authentication-Token":authKey},
                'url': "/workflow/" + workflowName + "/save",
                'data': workflowData,
                'success': function (data) {
                }
            });
        }
    }


    function loadWorkflow(workflowName) {

        currentWorkflow = workflowName;
        $("#currentWorkflowText").text(currentWorkflow);

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

        // Create the Cytoscape graph
        cy = cytoscape({
            container: document.getElementById('cy'),

            boxSelectionEnabled: false,
            autounselectify: false,
            wheelSensitivity: 0.1,
            style: [
                {
                    selector: 'node',
                    css: {
                        'content': 'data(label)',
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
                }
            ]
        });


        // Enable various Cytoscape extensions

        // Undo/Redo extension
        ur = cy.undoRedo({});

        // Panzoom extension
        cy.panzoom({});

        // Extension for drawing edges
        cy.edgehandles({
            preview: false,
            toggleOffOnLeave: true,
            complete: function( sourceNode, targetNodes, addedEntities ) {
                // The edge hendles extension is not integrated into the undo/redo extension.
                // So in order that adding edges is contained in the undo stack,
                // remove the edge just added and add back in again using the undo/redo
                // extension. Also add info to edge which is displayed when user clicks on it.
                for (var i=0; i<targetNodes.length; ++i) {
                    addedEntities[i].data('parameters', {
                        flags: [],
                        name: targetNodes[i].data().parameters.name,
                        nextStep: targetNodes[i].data().parameters.name
                    });
                }
                cy.remove(addedEntities); // Remove NOT using undo/redo extension
                var newEdges = ur.do('add',addedEntities); // Added back in using undo/redo extension
                newEdges.on('click', onClick);
            },
        });

        // Extension for copy and paste
        cy.clipboard();


        // Load the data into the graph
        workflowData = JSON.parse(workflowData);
        // If a node does not have a label field, set it to
        // the action. The label is what is displayed in the graph.
        workflowData = workflowData.map(function(value) {
            if (!value.data.hasOwnProperty("label")) {
                value.data.label = value.data.parameters.action;
            }
            return value;
        });

        cy.add(workflowData);

        // Setup the layout.
        // Setting up the layout must be done after loading the data. Otherwise
        // nodes will not be positioned correctly.
        cy.layout({
            name: 'breadthfirst',
            fit:true,
            padding: 5,
            root:"#start"
        });

        // Configure handler when user clicks on node or edge
        cy.$('*').on('click', onClick);

    }


    //-------------------------
    // Configure event handlers
    //-------------------------

    $(".nav-tabs a").click(function(){
        $(this).tab('show');
    });

    // Handle drops onto graph
    $( "#cy" ).droppable( {
        drop: handleDropEvent
    } );

    // Handle undo button press
    $( "#undo-button" ).click(function() {
        if (cy === null)
            return;

        ur.undo();
    });

    // Handle redo button press
    $( "#redo-button" ).click(function() {
        if (cy === null)
            return;

        ur.redo();
    });

    // Handle new button press
    $( "#new-button" ).click(function() {
        if (cy === null)
            return;

    });

    // Handle save button press
    $( "#save-button" ).click(function() {
        if (cy === null)
            return;

        saveWorkflow(currentWorkflow);
    });

    // Handle delete button press
    $( "#remove-button" ).click(function() {
        if (cy === null)
            return;

        removeSelectedNodes();
    });

    // Handle cut button press
    $( "#cut-button" ).click(function() {
        if (cy === null)
            return;

        cut();
    });

    // Handle cut button press
    $( "#copy-button" ).click(function() {
        if (cy === null)
            return;

        copy();
    });

    // Handle cut button press
    $( "#paste-button" ).click(function() {
        if (cy === null)
            return;

        paste();
    });

    // The following handler ensures the graph has the focus whenever you click on it so
    // that the undo/redo works when pressing Ctrl+Z/Ctrl+Y
    $( "#cy" ).on("mouseup mousedown", function(){
        $( "#cy" ).focus();
    });

    // Handle keyboard presses on graph
    $( "#cy" ).on("keydown", function (e) {
        if (cy === null)
            return;

        if(e.which === 46) { // Delete
            removeSelectedNodes();
        }
        else if (e.ctrlKey) {
            if (e.which === 90) // 'Ctrl+Z', Undo
                ur.undo();
            else if (e.which === 89) // 'Ctrl+Y', Redo
                ur.redo();
            else if (e.which == 67) // Ctrl + C, Copy
                copy();
            else if (e.which == 86) // Ctrl + V, Paste
                paste();
            else if (e.which == 88) // Ctrl + X, Cut
                cut();
            else if (e.which == 65) { // 'Ctrl+A', Select All
                cy.elements().select();
                e.preventDefault();
            }
        }
    });


    $("#executeWorkflowButton").on("click", function(e){
        if (cy === null)
            return;

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

    //--------------------
    // Setup Workflow list
    //--------------------

    // Download list of workflows for display in the Workflows list
    $.ajax({
        'async': true,
        'type': "GET",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "/workflows",
        'success': function (data) {
            $('#workflows').jstree({
                'core' : {
                    "check_callback" : true,
                    'multiple': false, // Disable multiple selection
                    'data' : formatWorkflowJsonDataForJsTree(data)
                },
                "plugins" : [ "contextmenu", "wholerow" ] // Show workflows as a list
                // of rows, not in tree form
            });
            // handle double click on workflow
            $("#workflows").bind("dblclick.jstree", function (event, data) {

                var node = $(event.target).closest("li");
                var node_id = node[0].id; //id of the selected node
                node = $('#workflows').jstree(true).get_node(node_id);

                var workflowName = node.text;

                // do something
                if (currentWorkflow)
                    saveWorkflow(currentWorkflow);

                loadWorkflow(workflowName);
            });
        }
    });


    //-------------------
    // Setup Actions tree
    //-------------------

    // Download all actions in all apps for display in the Actions tree
    $.ajax({
        'async': true,
        'type': "GET",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "/apps/actions",
        'success': function (data) {
            $('#actions').jstree({
                'core' : {
                    'data' : formatAppsActionJsonDataForJsTree(data)
                }
            })
            .bind("ready.jstree", function (event, data) {
                $(this).jstree("open_all"); // Expand all
            })
            .on('after_open.jstree', function (e, data) {
                for(var i = 0; i < data.node.children.length; i++) {
                    $("#"+data.node.children[i]).draggable( {
                        cursor: 'copy',
                        cursorAt: { left: 0, top: 0 },
                        containment: 'document',
                        helper: dragHelper
                    });
                }
            });
        }
    });

});
