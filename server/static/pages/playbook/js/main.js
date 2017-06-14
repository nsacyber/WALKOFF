$(function(){
    "use strict";

    $(".nav-tabs ul li a").each(function() {
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
    var startNode = null;
    var currentNodeInParametersEditor = null; // node being displayed in json editor

    //--------------------
    // Top level functions
    //--------------------

    // Reformat the JSON data returned from the /playbook endpoint
    // into a format that jsTree can understand.
    function formatWorkflowJsonDataForJsTree(data) {
        data = data.playbooks;
        workflowList = data;
        var jstreeData = [];
        _.each(data, function(workflows, playbookName) {
            var playbook = {};
            playbook.text = playbookName;
            playbook.children = [];
            _.each(workflows.sort(), function(workflowName) {
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
        appData = {};
        var jstreeData = [];
        _.each(data, function(actions, appName) {
            var app = {};
            app.text = appName;
            app.children = [];
            _.each(actions, function(actionProperties, actionName) {
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

    function getStartNode() {
        return startNode;
    }

    function setStartNode(start) {
        // If no start was given set it to one of the root nodes
        if (start) {
            startNode = start;
        }
        else {
            var roots = cy.nodes().roots();
            if (roots.size() > 0) {
                startNode = roots[0].data("parameters").name;
            }
        }
    }

    function createNodeSchema(parameters) {
        var appNames = [];
        if (!_.isEmpty(appData)) appNames = _.keys(appData);

        // This function creates a subschema for a single action. It contains
        // all the inputs of the action so the user only needs to enter the value.
        // When the user changes the action/flag/filter dropdown menu, the correct
        // number of inputs will be displayed in the form.
        function convertInputToSchema(args, inputName) {
            var subSchema = {
                type: "object",
                title: "Inputs",
                required: ['$action'],
                properties: {
                    $action: { // We need this to make sure each input is unique, since oneOf requires an exact match.
                        type: "string",
                        enum: [inputName],
                        options: {
                            hidden: true
                        }
                    }
                }
            };

            _.each(args, function(arg, index) {
                var pythonType = arg.type;
                var valueSchema = null;
                if (pythonType === "str") {
                    valueSchema = {
                        type: "string",
                        title: "Type: string"
                    };
                }
                else if (pythonType === "int") {
                    valueSchema = {
                        type: "integer",
                        title: "Type: integer"
                    };
                }
                else if (pythonType === "float") {
                    valueSchema = {
                        type: "number",
                        title: "Type: float"
                    };
                }
                else if (pythonType === "bool") {
                    valueSchema = {
                        type: "boolean",
                        format: "checkbox",
                        title: "Type: boolean"
                    };
                }

                subSchema.properties[arg.name] = {
                    type: "object",
                    title: "Input " + (index+1) + ": " + arg.name,
                    propertyOrder: index,
                    options: {
                        disable_collapse: true
                    },
                    properties: {
                        value: valueSchema,
                        key: { // This is hidden since it should not be modified by user
                            type: "string",
                            default: arg.name,
                            options: {
                                hidden: true
                            }
                        },
                        format: { // This is hidden since it should not be modified by user
                            type: "string",
                            default: pythonType,
                            options: {
                                hidden: true
                            }
                        }
                    }
                }
            });


            return subSchema;
        }

        var definitions = {};

        // Create the sub-schema for the actions
        var actions = appData[parameters.app].actions;
        var oneOfActions = [];
        _.each(actions, function(actionProperties, actionName) {
            var args = actionProperties.args;
            definitions["action_" + actionName] = convertInputToSchema(args, actionName);
            oneOfActions.push({
                $ref: "#/definitions/" + "action_" + actionName,
                title: actionName
            });
        });

        // Create the sub-schema for the flags
        var flags = flagsList;
        var oneOfFlags = [];
        _.each(flags, function(flagProperties, flagName) {
            var args = flagProperties.args;
            definitions["flag_" + flagName] = convertInputToSchema(args, flagName);
            oneOfFlags.push({
                $ref: "#/definitions/" + "flag_" + flagName,
                title: flagName
            });
        });

        // Create the sub-schema for the filters
        var filters = filtersList;
        var oneOfFilters = [];
        _.each(filters, function(filterProperties, filterName) {
            var args = filterProperties.args;
            definitions["filter_" + filterName] = convertInputToSchema(args, filterName);
            oneOfFilters.push({
                $ref: "#/definitions/" + "filter_" + filterName,
                title: filterName
            });
        });

        var schema = {
            $schema: "http://json-schema.org/draft-04/schema#",
            type: "object",
            title: "Node Parameters",
            definitions: definitions,
            required: ['name', 'start', 'app'],
            properties: {
                name: {
                    type: "string",
                    title: "Name",
                },
                start: {
                    type: "boolean",
                    title: "Set as Start Node",
                    format: "checkbox"
                },
                app: {
                    type: "string",
                    title: "App",
                    enum: appNames
                },
                device: {
                    type: "string",
                    title: "Device",
                    enum: appData[parameters.app].devices
                },
                // Note instead of having a separate action
                // property, we use a oneOf to include an
                // action plus its inputs in a subschema.
                // Similarly for flags and filters below.
                input: {
                    title: "Action",
                    oneOf: _.cloneDeep(oneOfActions)
                },
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
                                    args: {
                                        title: "Select Flag",
                                        oneOf: _.cloneDeep(oneOfFlags) // See comment above regarding action inputs
                                    },
                                    filters: {
                                        type: "array",
                                        title: "Filters",
                                        items: {
                                            type: "object",
                                            title: "Filter",
                                            properties: {
                                                args: {
                                                    title: "Select Filter",
                                                    oneOf: _.cloneDeep(oneOfFilters) // See comment above regarding action inputs
                                                },
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

    // Modify the parameters JSON object a little to conform to the schema expected by the parameters form
    function transformParametersToSchema(parameters) {
        parameters = _.cloneDeep(parameters);

        // We need to store a hidden property since in an oneOf,
        // the schema must match exactly one of the options. There
        // can be cases where two actions contain the exact same arguments,
        // so to distinguish the two actions place the action name in
        // in the $action property. This action is hidden and cannot be
        // modified by the user.
        parameters.input.$action = parameters.action;

        _.each(parameters.next, function(nextStep) {
            _.each(nextStep.flags, function(flag) {
                flag.args.$action = flag.action;

                _.each(flag.filters, function(filter) {
                    filter.args.$action = filter.action;
                });
            });
        });

        parameters.start = (getStartNode() === parameters.name);

        return parameters;
    }

    // Revert changes to the parameters JSON object of previous function
    function transformParametersFromSchema(parameters) {
        parameters = _.cloneDeep(parameters);

        parameters.action = parameters.input.$action;
        delete parameters.input.$action;

        _.each(parameters.next, function(nextStep) {
            _.each(nextStep.flags, function(flag) {
                flag.action = flag.args.$action;
                delete flag.args.$action;

                _.each(flag.filters, function(filter) {
                    filter.action = filter.args.$action;
                    delete filter.args.$action;
                });
            });
        });

        return parameters;
    }

    // This function displays a form next to the graph for editing a node when clicked upon
    function onNodeSelect(e) {
        var ele = e.cyTarget;

        currentNodeInParametersEditor = ele;

        $("#parametersBar").removeClass('hidden');
        var parameters = ele.data('parameters');
        $("#parameters").empty();

        parameters = transformParametersToSchema(parameters);

        //Omit the 'next' parameter, should only be edited when selecting an edge
        // var next = _.cloneDeep(parameters.next);
        // parameters = _.omit(parameters, ['next']);

        // Initialize the editor with a JSON schema
        var schema = createNodeSchema(parameters);
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
            required_by_default: false
        });

        editor.getEditor('root.app').disable();
        editor.getEditor('root.name').disable();

        // Hack: It appears this function is called as soon as you click on the node.
        // Therefore ignore the first time this function is called.
        var firstCall = true;
        editor.on('change',function() {
            if (firstCall) {
                firstCall = false;
                return;
            }
            var updatedParameters = editor.getValue();
            updatedParameters = transformParametersFromSchema(updatedParameters);
            //updatedParameters.next = next;

            ele.data('parameters', updatedParameters);
            ele.data('label', updatedParameters.action);
            setStartNode(updatedParameters.name);
        });
    }

    //TODO: bring up a separate JSON editor for "next" step information (filters/flags)
    function onEdgeSelect(event) {
        return;
    }

    function onUnselect(event) {
        if (!cy.$('node:selected').length) hideParameters();
    }
    
    // when an edge is removed, check the edges that still exist and remove the "next" steps for those that don't
    function onEdgeRemove(event) {
        var edgeData = event.cyTarget.data();
        // Do nothing if this is a temporary edge (edgehandles do not have paramters, and we mark temp edges on edgehandle completion)
        if (!edgeData.parameters || edgeData.parameters.temp) return;

        var parentNode = event.cyTarget.source();
        var parentData = _.cloneDeep(parentNode.data());

        parentData.parameters.next = _.reject(parentData.parameters.next, (next) => { return next.name === event.cyTarget.data().target; });
        parentNode.data(parentData);
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

        insertNode(app, action, x, y, true);
    }

    function insertNode(app, action, x, y, shouldUseRenderedPosition) {
        // Find next available id
        var id = 1;
        while (true) {
            var element = cy.getElementById(id.toString());
            if (element.length === 0)
                break;
            id += 1;
        }

        var inputs = {};
        var actionInfo = appData[app].actions[action];
        _.each(actionInfo.args, function(inputInfo) {

            var defaultValue;
            if (inputInfo.type === "str")
                defaultValue = "";
            else if (inputInfo.type === "bool")
                defaultValue = false;
            else
                defaultValue = 0;

            inputs[inputInfo.name] = {
                format: inputInfo.type,
                key: inputInfo.name,
                value: defaultValue
            };
        });

        // Add the node with the id just found to the graph in the location dropped
        // into by the mouse.
        var nodeToBeAdded = {
            group: 'nodes',
            data: {
                id: id.toString(),
                label: action,
                parameters: {
                    action: action,
                    app: app,
                    device: "",
                    errors: [],
                    input: inputs,
                    name: id.toString(),
                    next: [],
                }
            },
        };

        if (shouldUseRenderedPosition) nodeToBeAdded.renderedPosition = { x: x, y: y };
        else nodeToBeAdded.position = { x: x, y: y };
        
        var newNode = ur.do('add', nodeToBeAdded);
    }

    // This function removes selected nodes and edges
    function removeSelectedNodes() {
        var selecteds = cy.$(":selected");
        if (selecteds.length > 0)
            ur.do("remove", selecteds);
    }

    function onNodeAdded(event) {
        var node = event.cyTarget;
        // If the number of nodes in the graph is one, set the start node to it.
        if (node.isNode() && cy.nodes().size() === 1) {
            setStartNode(node.data("parameters").name);
        }
    }

    function onNodeRemoved(event) {
        var node = event.cyTarget;
        var parameters = node.data("parameters");
        // If the start node was deleted, set it to one of the roots of the graph
        if (parameters && node.isNode() && getStartNode() == parameters.name) {
            setStartNode();
        }
        // If an edge was deleted, delete the corresponding next
        // element in the node from which the edge originated.
        else if (node.isEdge()) {
            var source = node.source();
            var target = node.target();
            if (source.data("parameters") && target.data("parameters")) {
                var parameters = source.data("parameters");
                var next = parameters.next;
                var indexToDelete = -1;
                $.each(next, function( nextIndex, nextStep ) {
                    if (nextStep.name == target.data("parameters").name) {
                        indexToDelete = nextIndex;
                    }
                });
                if (indexToDelete >= 0) {
                    next.splice(indexToDelete, 1);
                    source.data("parameters", parameters);
                }
            }
        }

        if (currentNodeInParametersEditor == node)
            hideParameters();
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

        // Change the names of these new nodes so that they are the
        // same as the id. This is needed since only the name is
        // stored on the server and serves as the unique id of the
        // node. It therefore must be the same as the Cytoscape id.
        // Also delete the next field since user needs to explicitely
        // create new edges for the new node.
        for (var i=0; i<newNodes.length; ++i) {
            var parameters = newNodes[i].data("parameters");
            parameters.name = newNodes[i].data("id")
            parameters.next = [];
            newNodes[i].data("parameters", parameters);
        }
    }

    function renamePlaybook(oldPlaybookName, newPlaybookName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbooks/" + oldPlaybookName,
            'dataType': 'json',
            'contentType': 'application/json; charset=utf-8',
            'data': JSON.stringify({'new_name': newPlaybookName}),
            'success': function (data) {
                downloadWorkflowList();
                $.notify('Playbook ' + newPlaybookName + ' renamed successfully.', 'success');
            },
            'error': function (e) {
                $.notify('Playbook ' + newPlaybookName + ' could not be renamed.', 'error');
                console.log(e);
            }
        });
    }

    function duplicatePlaybook(oldPlaybookName, newPlaybookName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbooks/" + oldPlaybookName + "/copy",
            'dataType': 'json',
            'data': {playbook: newPlaybookName},
            'success': function (data) {
                downloadWorkflowList();
                $.notify('Playbook ' + newPlaybookName + ' duplicated successfully.', 'success');
            },
            'error': function (e) {
                $.notify('Playbook ' + newPlaybookName + ' could not be duplicated.', 'error');
                console.log(e);
            }
        });
    }

    function deletePlaybook(playbookName, workflowName) {
        $.ajax({
            'async': false,
            'type': "DELETE",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbooks/" + playbookName,
            'success': function (data) {
                downloadWorkflowList();

                if (currentPlaybook === playbookName)
                    closeCurrentWorkflow();

                $.notify('Playbook ' + playbookName + ' removed successfully.', 'success');
            },
            'error': function (e) {
                $.notify('Playbook ' + playbookName + ' could not be removed.', 'error');
                console.log(e);
            }
        });
    }

    function renameWorkflow(oldWorkflowName, playbookName, newWorkflowName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbooks/" + playbookName + "/workflows/" + oldWorkflowName,
            'dataType': 'json',
            'contentType': 'application/json; charset=utf-8',
            'data': JSON.stringify({'new_name': newWorkflowName}),
            'success': function (data) {
                downloadWorkflowList();
                $.notify('Workflow ' + newWorkflowName + ' renamed successfully.', 'success');
            },
            'error': function (e) {
                $.notify('Workflow ' + newWorkflowName + ' could not be renamed.', 'error');
                console.log(e);
            }
        });
    }

    function duplicateWorkflow(oldWorkflowName, playbookName, newWorkflowName) {
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbooks/" + playbookName + "/workflows/" + oldWorkflowName + "/copy",
            'dataType': 'json',
            'data': {playbook: playbookName, workflow: newWorkflowName},
            'success': function (data) {
                downloadWorkflowList();
                $.notify('Workflow ' + newWorkflowName + ' duplicated successfully.', 'success');
            },
            'error': function (e) {
                $.notify('Workflow ' + newWorkflowName + ' could not be duplicated.', 'error');
                console.log(e);
            }
        });
    }

    function deleteWorkflow(playbookName, workflowName) {
        $.ajax({
            'async': false,
            'type': "DELETE",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbooks/" + playbookName + "/workflows/" + workflowName,
            'success': function (data) {
                downloadWorkflowList();

                if (currentPlaybook === playbookName && currentWorkflow === workflowName)
                    closeCurrentWorkflow();

                $.notify('Workflow ' + workflowName + ' removed successfully.', 'success');
            },
            'error': function (e) {
                $.notify('Workflow ' + workflowName + ' could not be removed.', 'error');
                console.log(e);
            }
        });
    }

    function newWorkflow(playbookName, workflowName) {
        $.ajax({
            'async': false,
            'type': "PUT",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/playbooks/" + playbookName + "/workflows/" + workflowName,
            'success': function (data) {
                saveWorkflow(playbookName, workflowName, []);
                downloadWorkflowList();
                $.notify('Workflow ' + workflowName + ' added successfully.', 'success');
            },
            'error': function (e) {
                $.notify('Workflow ' + workflowName + ' could not be added.', 'error');
                console.log(e);
            }
        });
    }


    function saveWorkflow(playbookName, workflowName, workflowData) {
        var data = JSON.stringify({start: startNode, cytoscape: JSON.stringify(workflowData)});
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'dataType': 'json',
            'contentType': 'application/json; charset=utf-8',
            'headers':{"Authentication-Token":authKey},
            'url': "/playbooks/" + playbookName + "/workflows/" + workflowName + "/save",
            'data': data,
            'success': function (data) {
                $.notify('Workflow ' + workflowName + ' saved successfully.', 'success');
            },
            'error': function (e) {
                $.notify('Workflow ' + workflowName + ' could not be saved.', 'error');
                console.log(e);
            }
        });
    }

    function saveWorkflowJson(playbookName, workflowName, workflowDataEditor) {
        // Convert data in string format under JSON tab to a dictionary
        var dataJson = JSON.parse(workflowDataEditor);

        // Get current list of steps from cytoscape data in JSON format
        var workflowData = cy.elements().jsons();

        // Track existing steps using a dictionary where the keys are the
        // step ID and the values are the index of the step in workflowData
        var ids = {}
        for (var step = 0; step < workflowData.length; step++) {
            ids[workflowData[step].data.id] = step.toString();
        }

        // Compare current list of steps with updated list and modify current list
        var stepsJson = dataJson.steps; // Get updated list of steps
        stepsJson.forEach(function(stepJson) {
            var idJson = stepJson.data.id;
            if (idJson in ids) {
                // If step already exists, then just update its fields
                var step = Number(ids[idJson])
                workflowData[step].data = stepJson.data;
                workflowData[step].group = stepJson.group;
                workflowData[step].position = stepJson.position;
                // Delete step id
                delete ids[idJson]
            } else {
                // If step is absent, then create a new step
                var newStep = getStepTemplate();
                newStep.data = stepJson.data;
                newStep.group = stepJson.group;
                newStep.position = stepJson.position;
                // Add new step
                workflowData.push(newStep)
            }
        })

        if (Object.keys(ids).length > 0) {
            // If steps have been removed, then delete steps
            for (id in Object.keys(ids)) {
                var step = Number(ids[idJson])
                workflowData.splice(step, 1)
            }
        }

        // Save updated cytoscape data in JSON format
        saveWorkflow(playbookName, workflowName, workflowData)
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
                'url': "/playbooks/" + currentPlaybook + "/workflows/" + currentWorkflow,
                'success': function (data) {
                    tmp = data;
                },
                'error': function (e) {
                    $.notify('Workflow ' + currentWorkflow + ' could not be loaded properly.', 'error');
                    console.log(e);
                }
            });
            return tmp;
        }();

        // Remove instructions
        hideInstructions();

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
                var sourceParameters = sourceNode.data().parameters;
                if (!sourceParameters.hasOwnProperty("next"))
                    sourceParameters.next = [];

                // The edge handles extension is not integrated into the undo/redo extension.
                // So in order that adding edges is contained in the undo stack,
                // remove the edge just added and add back in again using the undo/redo
                // extension. Also add info to edge which is displayed when user clicks on it.
                for (var i=0; i<targetNodes.length; i++) {
                    addedEntities[i].data('parameters', {
                        flags: [],
                        name: targetNodes[i].data().parameters.name,
                        nextStep: targetNodes[i].data().parameters.name,
                        temp: true
                    });

                    //If we attempt to draw an edge that already exists, please remove it and take no further action
                    if (_.find(sourceParameters.next, (next) => { return next.name === targetNodes[i].data().id })) {
                        cy.remove(addedEntities);
                        return;
                    }

                    sourceParameters.next.push({
                        flags: [],
                        name: targetNodes[i].data().id // Note use id, not name since name can be changed
                    });

                    sourceNode.data('parameters', sourceParameters);
                }

                cy.remove(addedEntities);

                _.each(addedEntities, function (ae) {
                    var data = ae.data();
                    delete data.parameters.temp;
                    ae.data(data);
                });

                var newEdges = ur.do('add',addedEntities); // Added back in using undo/redo extension
            },
        });

        // Extension for copy and paste
        cy.clipboard();

        //Extension for grid and guidelines
        cy.gridGuide({
            // drawGrid: true,
            // strokeStyle: '#222'
            //options...
        });

        //var contextMenusInstance = cy.contextMenus();

        // var edgeBendEditingInstance = cy.edgeBendEditing({
        //     // this function specifies the positions of bend points
        //     bendPositionsFunction: function(ele) {
        //         return ele.data('bendPointPositions');
        //     },
        //     // whether to initilize bend points on creation of this extension automatically
        //     initBendPointsAutomatically: true,
        //     // whether the bend editing operations are undoable (requires cytoscape-undo-redo.js)
        //     undoable: true,
        //     // the size of bend shape is obtained by multipling width of edge with this parameter
        //     bendShapeSizeFactor: 6,
        //     // whether to start the plugin in the enabled state
        //     enabled: true,
        //     // title of add bend point menu item (User may need to adjust width of menu items according to length of this option)
        //     addBendMenuItemTitle: "Add Bend Point",
        //     // title of remove bend point menu item (User may need to adjust width of menu items according to length of this option)
        //     removeBendMenuItemTitle: "Remove Bend Point"
        // });

        // Load the data into the graph
        // If a node does not have a label field, set it to
        // the action. The label is what is displayed in the graph.
        var steps = workflowData.steps.map(function(value) {
            if (!value.data.hasOwnProperty("label")) {
                value.data.label = value.data.parameters.action;
            }
            return value;
        });

        cy.add(steps);

        cy.fit(50);

        setStartNode(workflowData.start);

        // Configure handler when user clicks on node or edge
        cy.on('select', 'node', onNodeSelect);
        cy.on('select', 'edge', onEdgeSelect);
        cy.on('unselect', onUnselect);

        // Configure handlers when nodes/edges are added or removed
        cy.on('add', 'node', onNodeAdded);
        cy.on('remove', 'node', onNodeRemoved);
        cy.on('remove', 'edge', onEdgeRemove);

        $("#cy-json-data").val(JSON.stringify(workflowData, null, 2));

    }


    function closeCurrentWorkflow() {
        $("#cy").empty();
        $("#currentWorkflowText").text("");
        hideParameters();
        showInstruction();
    }

    function showInstruction() {
        var cyInstructions = $( "#cy-instructions-template" ).clone().removeClass('hidden');
        cyInstructions.attr("id", "cy-instructions");
        $("#cy").append(cyInstructions);
    }

    function hideInstructions() {
        $("#cy-instructions").remove();
    }

    function hideParameters() {
        $("#parametersBar").addClass('hidden');
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
                            showDialog("Rename Workflow",
                                       "Playbook Name",
                                       playbookName,
                                       true,
                                       "Workflow Name",
                                       workflowName,
                                       false,
                                       renameCallback,
                                       checkIfWorkflowExists);
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
                            showDialog("Rename Playbook",
                                       "Playbook Name",
                                       playbookName,
                                       false,
                                       "",
                                       "",
                                       true,
                                       renameCallback,
                                       checkIfPlaybookExists);
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
            'url': "/playbooks",
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
                // handle double click on workflow, load workflow graph for editing
                $("#workflows").bind("dblclick.jstree", function (event, data) {

                    var node = $(event.target).closest("li");
                    var node_id = node[0].id; //id of the selected node
                    node = $('#workflows').jstree(true).get_node(node_id);

                    var workflowName = node.text;
                    if (node.data && node.data.playbook) {
                        loadWorkflow(node.data.playbook, workflowName);

                        // hide parameters panel until first click on node
                        hideParameters();
                    }
                });
                // handle double click on workflow, add action node to center of canvas
                $('#actions').bind("dblclick.jstree", function (event, data) {
                    if (cy === null)
                        return;

                    var node = $(event.target).closest("li");
                    var node_id = node[0].id; //id of the selected node
                    node = $('#actions').jstree(true).get_node(node_id);

                    if (!node.data)
                        return;
                        
                    var app = node.data.app;
                    var action = node.text;
                    var extent = cy.extent();

                    function avg(a, b) { return (a + b) / 2; }

                    insertNode(app, action, avg(extent.x1, extent.x2), avg(extent.y1, extent.y2), false);
                });
            },
            'error': function (e) {
                $.notify('Error retrieving playbooks.', 'error');
                console.log(e);
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
    function showDialog(title,
                        label1Text,
                        input1Text,
                        isInput1Hidden,
                        label2Text,
                        input2Text,
                        isInput2Hidden,
                        submitCallback,
                        validateCallback) {

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
                valid = valid && checkLength( input1, label1Text, 1, 50 );
            if (!isInput2Hidden)
                valid = valid && checkLength( input2, label2Text, 1, 50 );
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
        showDialog("Create New Workflow",
                   "Playbook Name",
                   "",
                   false,
                   "Workflow Name",
                   "",
                   false,
                   newWorkflow,
                   checkIfWorkflowExists);
    });

    // Handle save button press
    $( "#save-button" ).click(function() {
        if (cy === null)
            return;

        if ($("#playbookEditorTabs ul li.ui-state-active").index() == 0) {
            // If the graphical editor tab is active
            saveWorkflow(currentPlaybook, currentWorkflow, cy.elements().jsons());
        } else {
            // If the JSON tab is active
            saveWorkflowJson(currentPlaybook, currentWorkflow, document.getElementById('cy-json-data').value);
        }
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
            //TODO: re-enable undo/redo once we restructure how next steps / edges are stored
            // if (e.which === 90) // 'Ctrl+Z', Undo
            //     ur.undo();
            // else if (e.which === 89) // 'Ctrl+Y', Redo
            //     ur.redo();
            if (e.which == 67) // Ctrl + C, Copy
                copy();
            else if (e.which == 86) // Ctrl + V, Paste
                paste();
            else if (e.which == 88) // Ctrl + X, Cut
                cut();
            // else if (e.which == 65) { // 'Ctrl+A', Select All
            //     cy.elements().select();
            //     e.preventDefault();
            // }
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
            _.each(appData, function(actions, appName) {
                $.ajax({
                    'async': false,
                    'type': "GET",
                    'global': false,
                    'headers':{"Authentication-Token":authKey},
                    'url': "/apps/" + appName + "/devices",
                    'dataType': 'json',
                    'contentType': 'application/json; charset=utf-8',
                    'data': {},
                    'success': function (data) {
                        appData[appName].devices = [];
                        _.each(data, function(value) {
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
            flagsList = data.flags;
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
            filtersList = data.filters;
        }
    });

    //---------------------------------
    // Other setup
    //---------------------------------
    showInstruction();

    $("#playbookEditorTabs UL LI A").each(function() {
        $(this).attr("href", location.href.toString()+$(this).attr("href"));
    });
    $("#playbookEditorTabs").tabs();

    function getStepTemplate() {
        return {
            "classes": "",
            "data": {},
            "grabbable": true,
            "group": "",
            "locked": false,
            "position": {},
            "removed": false,
            "selectable": true,
            "selected": false
        };
    }
});
