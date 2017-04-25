$(function(){
    "use strict";

    $(".nav-tabs ul li a").each(function() {
        console.log("HERE");
        $(this).attr("href", location.href.toString()+$(this).attr("href"));
    });

    //--------------------
    // Top level variables
    //--------------------

    var currentPlaybook = null;
    var currentWorkflow = null;
    var workflowList = null;
    var cy = null;
    var ur = null;
    var appData = null;
    var flagsList = [];
    var filtersList = [];

    //--------------------
    // Top level functions
    //--------------------

    // Reformat the JSON data returned from the /playbook endpoint
    // into a format that jsTree can understand.
    function formatWorkflowJsonDataForJsTree(data) {
        data = JSON.parse(data).playbooks;
        workflowList = data;
        var jstreeData = [];
        $.each(data, function( playbookName, workflows ) {
            var playbook = {};
            playbook.text = playbookName;
            playbook.children = [];
            $.each(workflows.sort(), function( index, workflowName ) {
                playbook.children.push({text: workflowName, icon: "jstree-file", data: {playbook: playbookName}});
            });
            jstreeData.push(playbook);
        });

        // Sort jstreeData by playbook name
        jstreeData = jstreeData.sort(function(a, b){
            return a.text.localeCompare(b.text);
        });

        return jstreeData;
    }


    // Reformat the JSON data returned from the /apps/actions endpoint
    // into a format that jsTree can understand.
    function formatAppsActionJsonDataForJsTree(data) {
        data = JSON.parse(data);
        appData = {};
        var jstreeData = [];
        $.each(data, function( appName, actions ) {
            var app = {};
            app.text = appName;
            app.children = [];
            $.each(actions, function( actionName, actionProperties ) {
                app.children.push({text: actionName, icon: "jstree-file", data: {app: appName}});
            });

            // Sort children by action name
            app.children = app.children.sort(function(a, b){
                return a.text.localeCompare(b.text);
            });

            jstreeData.push(app);

            appData[appName] = {actions: actions};
        });

        // Sort jstreeData by app name
        jstreeData = jstreeData.sort(function(a, b){
            return a.text.localeCompare(b.text);
        });

        return jstreeData;
    }


    function createSchema(parameters) {
        var appNames = [];
        var appActions = {};
        $.each(appData, function( appName, value ) {
            appNames.push(appName);
            appActions[appName] = [];
            $.each(value.actions, function( actionName, actionProperties ) {
                appActions[appName].push(actionName);
            });
        });

        // Create a schema

        var argProperties = {
            type: "array",
            title: "Inputs",
            format: "table",
            items: {
                type: "object",
                id: "arr_item",
                options: {
                    disable_collapse: true
                },
                properties: {
                    key: {
                        type: "string",
                        title: "Input Name"
                    },
                    format: {
                        type: "string",
                        options: {
                            hidden: true
                        }
                    },
                    value: {
                        type: "string",
                        title: "Input Value"
                    }
                }
            }
        };

        var schema = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            type: "object",
            title: "Node Parameters",
            properties: {
                name: {
                    type: "string",
                    title: "Name",
                },
                app: {
                    type: "string",
                    title: "App",
                    enum: appNames
                },
                action: {
                    type: "string",
                    title: "Action",
                    enum: appActions[parameters.app]
                },
                device: {
                    type: "string",
                    title: "Device",
                    enum: appData[parameters.app].devices
                },
                input: deepcopy(argProperties),
                next: {
                    options: {
                        hidden: true
                    }
                },
                errors: {
                    options: {
                        hidden: true
                    }
                }
            }
        };


        var numSteps = parameters.next.length;
        if (numSteps > 0) {
            schema.properties.next = {
                type: "array",
                title: "Next Nodes",
                options: {
                    disable_array_add: true,
                    disable_array_delete: true,
                    disable_array_reorder: true
                },
                items: {
                    type: "object",
                    headerTemplate: "Next Node {{ i1 }}: {{ self.name }}",
                    properties: {
                        name: {
                            type: "string",
                            options: {
                                hidden: true
                            }
                        },
                        flags: {
                            type: "array",
                            headerTemplate: "Flags",
                            items: {
                                type: "object",
                                title: "Next Step Flag",
                                headerTemplate: "Flag {{ i1 }}",
                                properties: {
                                    action: {
                                        type: "string",
                                        title: "Select Flag",
                                        enum: flagsList
                                    },
                                    args: deepcopy(argProperties),
                                    filters: {
                                        type: "array",
                                        title: "Filters",
                                        items: {
                                            type: "object",
                                            title: "Filter",
                                            properties: {
                                                action: {
                                                    type: "string",
                                                    title: "Select Filter",
                                                    enum: filtersList
                                                },
                                                args: deepcopy(argProperties),
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            };
        }

        return schema;
    }

    function deepcopy(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    // Modify the parameters JSON object a little to conform to the schema expected by the parameters form
    function transformParametersToSchema(parameters) {
        parameters = deepcopy(parameters);

        var newInputs = [];
        $.each(parameters.input, function( key, input ) {
            newInputs.push(input);
        });
        parameters.input = newInputs;

        $.each(parameters.next, function( nextIndex, nextStep ) {
            $.each(nextStep.flags, function( index, flag ) {

                var newArgs = [];
                $.each(flag.args, function( key, arg ) {
                    newArgs.push(arg);
                });
                flag.args = newArgs;

                $.each(flag.filters, function( index, filter ) {
                    var newArgs = [];
                    $.each(filter.args, function( key, arg ) {
                        newArgs.push(arg);
                    });
                    filter.args = newArgs;
                });
            });
        });

        return parameters;
    }

    // Revert changes to the parameters JSON object of previous function
    function transformParametersFromSchema(parameters) {
        parameters = deepcopy(parameters);

        var newInputs = {};
        $.each(parameters.input, function( index, input ) {
            newInputs[input.key] = input;
        });
        parameters.input = newInputs;

        $.each(parameters.next, function( nextIndex, nextStep ) {
            $.each(nextStep.flags, function( index, flag ) {

                var newArgs = {};
                $.each(flag.args, function( index, arg ) {
                    newArgs[arg.key] = arg;
                });
                flag.args = newArgs;

                $.each(flag.filters, function( index, filter ) {
                    var newArgs = {};
                    $.each(filter.args, function( index, arg ) {
                        newArgs[arg.key] = arg;
                    });
                    filter.args = newArgs;
                });
            });
        });

        return parameters;
    }

    // This function displays a form next to the graph for editing a node/edge when clicked upon
    function onClick(e) {
        var ele = e.cyTarget;

        // Ignore edges for now.
        if (ele.isEdge()) {
            return;
        }

        var parameters = ele.data('parameters');
        $("#parameters").removeClass('hidden');
        $("#parameters").empty();

        console.log(parameters)
        parameters = transformParametersToSchema(parameters);
        console.log(parameters);
        // Initialize the editor with a JSON schema
        var schema = createSchema(parameters);
        JSONEditor.defaults.options.theme = 'bootstrap3';
        JSONEditor.defaults.options.iconlib = "bootstrap3";
        var editor = new JSONEditor(document.getElementById('parameters'),{
            schema: schema,

            startval: parameters,

            disable_edit_json: true,

            disable_properties: true,

            // Disable additional properties
            no_additional_properties: true,

            // Require all properties by default
            required_by_default: true
        });

        editor.getEditor('root.app').disable();
        editor.getEditor('root.name').disable();

        editor.on('change',function() {
            var updatedParameters = editor.getValue();
            updatedParameters = transformParametersFromSchema(updatedParameters);
            ele.data('parameters', updatedParameters);
            ele.data('label', updatedParameters.action);
        });
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
        if (!draggableNode.data)
            return;
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
                    errors: [],
                    input: {},
                    name: id.toString(),
                    next: [],
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

    function renamePlaybook(oldPlaybookName, newPlaybookName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook/" + oldPlaybookName + "/edit",
            'dataType': 'json',
            'contentType': 'application/json; charset=utf-8',
            'data': JSON.stringify({'new_name': newPlaybookName}),
            'success': function (data) {
                downloadWorkflowList();
            }
        });
    }

    function duplicatePlaybook(oldPlaybookName, newPlaybookName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook/" + oldPlaybookName + "/copy",
            'dataType': 'json',
            'data': {playbook: newPlaybookName},
            'success': function (data) {
                downloadWorkflowList();
            }
        });
    }

    function deletePlaybook(playbookName, workflowName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook/" + playbookName + "/delete",
            'success': function (data) {
                downloadWorkflowList();
            }
        });
    }

    function renameWorkflow(oldWorkflowName, playbookName, newWorkflowName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook/" + playbookName + "/" + oldWorkflowName + "/edit",
            'dataType': 'json',
            'contentType': 'application/json; charset=utf-8',
            'data': JSON.stringify({'new_name': newWorkflowName}),
            'success': function (data) {
                downloadWorkflowList();
            }
        });
    }

    function duplicateWorkflow(oldWorkflowName, playbookName, newWorkflowName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook/" + playbookName + "/" + oldWorkflowName + "/copy",
            'dataType': 'json',
            'data': {playbook: playbookName, workflow: newWorkflowName},
            'success': function (data) {
                downloadWorkflowList();
            }
        });
    }

    function deleteWorkflow(playbookName, workflowName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook/" + playbookName + "/" + workflowName + "/delete",
            'success': function (data) {
                downloadWorkflowList();
            }
        });
    }

    function newWorkflow(playbookName, workflowName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook/" + playbookName + "/" + workflowName + "/add",
            'success': function (data) {
                saveWorkflow(playbookName, workflowName, []);
                downloadWorkflowList();
            }
        });
    }


    function saveWorkflow(playbookName, workflowName, workflowData) {
        var data = JSON.stringify({filename: "", cytoscape: JSON.stringify(workflowData)});
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'dataType': 'json',
            'contentType': 'application/json; charset=utf-8',
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook/" + playbookName + "/" + workflowName + "/save",
            'data': data,
            'success': function (data) {
            }
        });
    }


    function loadWorkflow(playbookName, workflowName) {

        currentPlaybook = playbookName;
        currentWorkflow = workflowName;
        $("#currentWorkflowText").text(currentWorkflow);

        var workflowData = function () {
            var tmp = null;
            $.ajax({
                'async': false,
                'type': "GET",
                'global': false,
                'headers':{"Authentication-Token":authKey},
                'url': "/playbook/" + currentPlaybook + "/" + currentWorkflow + "/display",
                'success': function (data) {
                    tmp = data;
                }
            });
            return tmp;
        }();

        // Remove instructions
        $("#cy-instructions").addClass('hidden');

        // Create the Cytoscape graph
        cy = cytoscape({
            container: document.getElementById('cy'),

            boxSelectionEnabled: false,
            autounselectify: false,
            wheelSensitivity: 0.1,
            layout: { name: 'preset' },
            style: [
                {
                    selector: 'node',
                    css: {
                        'content': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'shape': 'roundrectangle',
                        //'background-color': '#aecbdc',
                        'selection-box-color': 'red',
                        'font-family': 'Oswald',
                        'font-weight': 'lighter',
                        'font-size': '15px',
                        'width':'40',
                        'height':'40'
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

                    //Update the next property of the source node to contain the new next steps
                    var parameters = sourceNode.data().parameters;
                    if (!parameters.hasOwnProperty("next"))
                        parameters.next = [];

                    // If for some reason, the next array already
                    // contains an item with the same next node as
                    // this new link (probably due to some bug),
                    // remove it now
                    parameters.next.filter(function(next) {
                        return next.name !== targetNodes[i].data().id;
                    });

                    parameters.next.push({
                        flags: [],
                        name: targetNodes[i].data().id // Note use id, not name since name can be changed
                    });
                    sourceNode.data('parameters', parameters);
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
        workflowData = workflowData.steps.map(function(value) {
            if (!value.data.hasOwnProperty("label")) {
                value.data.label = value.data.parameters.action;
            }
            return value;
        });

        cy.add(workflowData);

        cy.fit();

        // Configure handler when user clicks on node or edge
        cy.$('*').on('click', onClick);

    }


    // Download list of workflows for display in the Workflows list
    function downloadWorkflowList() {

        function customMenu(node) {
            if (node.data && node.data.playbook) {
                var playbookName = node.data.playbook;
                var workflowName = node.text;
                var items = {
                    renameItem: { // The "rename" menu item
                        label: "Rename Workflow",
                        action: function () {
                            var renameCallback = renameWorkflow.bind(null, workflowName);
                            showDialog("Raname Workflow", "Playbook Name", playbookName, true, "Workflow Name", workflowName, false, renameCallback, checkIfWorkflowExists);
                        }
                    },
                    duplicateItem: { // The "duplicate" menu item
                        label: "Duplicate Workflow",
                        action: function () {
                            var duplicateCallback = duplicateWorkflow.bind(null, workflowName);
                            showDialog("Duplicate Workflow",
                                       "Playbook Name",
                                       playbookName,
                                       true,
                                       "Workflow Name",
                                       workflowName,
                                       false,
                                       duplicateCallback,
                                       checkIfWorkflowExists);
                        }
                    },
                    deleteItem: { // The "delete" menu item
                        label: "Delete Workflow",
                        action: function () {
                            deleteWorkflow(playbookName, workflowName);
                        }
                    }
                };

                return items;
            }
            else {
                var playbookName = node.text;
                var items = {
                    renameItem: { // The "rename" menu item
                        label: "Rename Playbook",
                        action: function() {
                            var renameCallback = renamePlaybook.bind(null, playbookName);
                            showDialog("Raname Playbook", "Playbook Name", playbookName, false, "", "", true, renameCallback, checkIfPlaybookExists);
                        }
                    },
                    duplicateItem: { // The "duplicate" menu item
                        label: "Duplicate Playbook",
                        action: function() {
                            var duplicateCallback = duplicatePlaybook.bind(null, playbookName);
                            showDialog("Duplicate Playbook",
                                       "Playbook Name",
                                       playbookName, false,
                                       "",
                                       "",
                                       true,
                                       duplicateCallback,
                                       checkIfPlaybookExists);
                        }
                    },
                    deleteItem: { // The "delete" menu item
                        label: "Delete Playbook",
                        action: function() {
                            deletePlaybook(playbookName);
                        }
                    }
                };

                return items;
            }
        }

        $.ajax({
            'async': true,
            'type': "GET",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbook",
            'success': function (data) {
                if ($("#workflows").jstree(true))
                    $("#workflows").jstree(true).destroy();
                $('#workflows').jstree({
                    'core' : {
                        "check_callback" : true,
                        'multiple': false, // Disable multiple selection
                        'data' : formatWorkflowJsonDataForJsTree(data)
                    },
                    "plugins" : [ "contextmenu" ],
                    "contextmenu" : { items: customMenu }
                })
                    .bind("ready.jstree", function (event, data) {
                        $(this).jstree("open_all"); // Expand all
                    });
                // handle double click on workflow
                $("#workflows").bind("dblclick.jstree", function (event, data) {

                    var node = $(event.target).closest("li");
                    var node_id = node[0].id; //id of the selected node
                    node = $('#workflows').jstree(true).get_node(node_id);

                    var workflowName = node.text;
                    if (node.data && node.data.playbook) {
                        loadWorkflow(node.data.playbook, workflowName);

                        // hide parameters panel until first click on node
                        $("#parameters").addClass('hidden');
                    }
                });
            }
        });
    }


    function checkIfPlaybookExists(playbookName) {
        if(workflowList.hasOwnProperty(playbookName)) {
            return {
                result: false,
                error: 'Playbook "' + playbookName + '" already exists.'
            };
        }
        else {
            return {
                result: true,
                error: null
            };
        }
    }

    function checkIfWorkflowExists(playbookName, workflowName) {
        if (workflowList.hasOwnProperty(playbookName) &&
            workflowList[playbookName].indexOf(workflowName) >= 0) {
            return {
                result: false,
                error: 'Workflow "' + workflowName + '" already exists.'
            };
        }
        else {
            return {
                result: true,
                error: null
            };
        }
    }


    // The following function popups a dialog to be used for creating,
    // renaming and duplicating playbooks and workflows.
    function showDialog(title, label1Text, input1Text, isInput1Hidden, label2Text, input2Text, isInput2Hidden, submitCallback, validateCallback) {

        var dialog = $( "#dialog-template" ).clone().removeClass('hidden');

        var label1 = dialog.find( ".label1" );
        var input1 = dialog.find( ".input1" );
        var label2 = dialog.find( ".label2" );
        var input2 = dialog.find( ".input2" );
        var allFields = $( [] ).add( input1 ).add( input2 );
        var tips = dialog.find( ".validateTips" );

        dialog.attr("title", title);
        label1.text(label1Text);
        input1.val(input1Text);
        label2.text(label2Text);
        input2.val(input2Text);
        if (isInput1Hidden) {
            label1.addClass('hidden');
            input1.addClass('hidden');
        }
        else if (isInput2Hidden) {
            label2.addClass('hidden');
            input2.addClass('hidden');
        }

        function updateTips( t ) {
            tips
                .text( t )
                .addClass( "ui-state-highlight" );
            setTimeout(function() {
                tips.removeClass( "ui-state-highlight", 1500 );
            }, 500 );
        }

        function checkLength( o, n, min, max ) {
            if ( o.val().length > max || o.val().length < min ) {
                o.addClass( "ui-state-error" );
                updateTips( "Length of " + n + " must be between " +
                            min + " and " + max + " characters." );
                return false;
            } else {
                return true;
            }
        }

        function customValidation(value1, value2) {
            var result = validateCallback(value1, value2);
            if (result.result) {
                return true;
            }
            else {
                updateTips(result.error);
                return false;
            }
        }

        function closeDialog() {
            dialog.dialog("close");
            dialog.remove();
        }

        $('form').on('submit', function(event){
            event.preventDefault();
        });

        var buttons = {};
        buttons[title] = function() {
            var valid = true;
            allFields.removeClass( "ui-state-error" );

            if (!isInput1Hidden)
                valid = valid && checkLength( input1, label1Text, 1, 255 );
            if (!isInput2Hidden)
                valid = valid && checkLength( input2, label2Text, 1, 255 );
            valid = valid && customValidation(input1.val(), input2.val());
            if (valid) {
                submitCallback(input1.val(), input2.val());
                closeDialog();
            }
        };
        buttons["Cancel"] = function() {
            closeDialog();
        };

        dialog.dialog({
            autoOpen: false,
            modal: true,
            dialogClass: "no-close",
            buttons: buttons
        });

        dialog.dialog( "open" );
    }


    //-------------------------
    // Configure event handlers
    //-------------------------
    $("#palette ul li a").each(function() {
        console.log("CHANGED HREF");
        $(this).attr("href", location.href.toString()+$(this).attr("href"));
    });

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
        $("#workflows-tab").tab('show');
        showDialog("Create New Workflow", "Playbook Name", "", false, "Workflow Name", "", false, newWorkflow, checkIfWorkflowExists);
    });

    // Handle save button press
    $( "#save-button" ).click(function() {
        if (cy === null)
            return;

        saveWorkflow(currentPlaybook, currentWorkflow, cy.elements().jsons());
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


    //---------------------------------
    // Setup Workflows and Actions tree
    //---------------------------------

    // Download all workflows for display in the Workflows tree
    downloadWorkflowList();

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

            // Now is a good time to download all devices for all apps
            $.each(appData, function( appName, actions ) {
                $.ajax({
                    'async': false,
                    'type': "POST",
                    'global': false,
                    'headers':{"Authentication-Token":authKey},
                    'url': "/configuration/" + appName + "/devices",
                    'dataType': 'json',
                    'contentType': 'application/json; charset=utf-8',
                    'data': {},
                    'success': function (data) {
                        appData[appName].devices = [];
                        $.each(data, function( index, value ) {
                            appData[appName].devices.push(value.name);
                        });
                    }
                });
            });
        }
    });

    // Download list of all flags
    $.ajax({
        'async': false,
        'type': "GET",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "/flags",
        'dataType': 'json',
        'success': function (data) {
            flagsList = [];
            $.each(data.flags, function( key, value ) {
                flagsList.push(key);
            });
        }
    });

    // Download list of all filters
    $.ajax({
        'async': false,
        'type': "GET",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "/filters",
        'dataType': 'json',
        'success': function (data) {
            filtersList = [];
            $.each(data.filters, function( key, value ) {
                filtersList.push(key);
            });
        }
    });
});
