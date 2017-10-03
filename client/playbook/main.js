

$(function(){
    "use strict";

    //--------------------
    // Top level variables
    //--------------------

    var workflowsForPlaybooks = null;
    var cy = null;
    var ur = null;
    var actionsForApps = null;
    var flagsList = [];
    var filtersList = [];
    var startNode = null;
    var offsetX = -330;
    var offsetY = -170;
    var currentNodeInParametersEditor = null; // node being displayed in json editor
    
    //--------------------
    // Top level functions
    //--------------------

    // Reformat the JSON data returned from the /playbook endpoint
    // into a format that jsTree can understand.
    function formatWorkflowJsonDataForJsTree(data) {
        workflowsForPlaybooks = data;
        var jstreeData = [];
        _.each(data, function(playbook) {
            var jsTreePlaybook = {};
            jsTreePlaybook.text = playbook.name;
            jsTreePlaybook.children = [];
            _.each(playbook.workflows, function(workflow) {
                jsTreePlaybook.children.push({text: workflow.name, icon: "jstree-file", data: {playbook: playbook.name}});
            });
            jstreeData.push(jsTreePlaybook);
        });

        // Sort jstreeData by playbook name
        jstreeData = jstreeData.sort(function(a, b){
            return a.text.localeCompare(b.text);
        });

        return jstreeData;
    }


    // Reformat the JSON data returned from the /api/apps/actions endpoint
    // into a format that jsTree can understand.
    function formatAppsActionJsonDataForJsTree(data) {
        actionsForApps = {};
        var jstreeData = [];
        _.each(data, function(actions, appName) {
            var app = {};
            app.text = appName;
            app.children = [];
            _.each(actions, function(actionProperties, actionName) {
                var child = {text: actionName, icon: "jstree-file", data: {app: appName}};
                if (actionProperties.description) child.a_attr = { title: actionProperties.description };
                app.children.push(child);
            });

            // Sort children by action name
            app.children = app.children.sort(function(a, b){
                return a.text.localeCompare(b.text);
            });

            jstreeData.push(app);

            actionsForApps[appName] = {actions: actions};
        });

        // Sort jstreeData by app name
        jstreeData = jstreeData.sort(function(a, b){
            return a.text.localeCompare(b.text);
        });

        return jstreeData;
    }

    function createNodeSchema(parameters) {
        var appNames = [];
        if (!_.isEmpty(actionsForApps)) appNames = _.keys(actionsForApps);

        // This function creates a subschema for a single action. It contains
        // all the inputs of the action so the user only needs to enter the value.
        // When the user changes the action/flag/filter dropdown menu, the correct
        // number of inputs will be displayed in the form.
        function convertInputToSchema(args, inputName) {
            var subSchema = {
                type: "object",
                // type: "array",
                title: "Inputs",
                required: ['$action'],
                options: { hidden: args.length === 0 },
                //Items populated below
                // items: []
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
                var input = _.cloneDeep(arg);
                var inputName = input.name;
                delete input.name;

                //Hack: allow for output references "@<step_name>" for number fields
                if (input.type === "number" || input.type === "integer") input.type = "string";

                // TODO: really we shouldn't need to grab type from under 'schema'; this is just here to support a backend change
                // should be removed once the backend is fixed to correct the validation of objects
                if (input.type === "object" || (input.schema && input.schema.type === "object")) {
                    if (input.schema && !input.type) input.type = input.schema.type;
                    input.options = input.options || {};
                    input.options.disable_properties = false;
                    input.additionalProperties = true;
                }

                input.title = "Type: " + input.type;

                // var valueSchema = null;
                // if (pythonType === "string") {
                //     valueSchema = {
                //         type: "string",
                //         title: "Type: string"
                //     };
                // }
                // else if (pythonType === "integer") {
                //     valueSchema = {
                //         type: "integer",
                //         title: "Type: integer"
                //     };
                // }
                // else if (pythonType === "number") {
                //     valueSchema = {
                //         type: "number",
                //         title: "Type: float"
                //     };
                // }
                // else if (pythonType === "boolean") {
                //     valueSchema = {
                //         type: "boolean",
                //         format: "checkbox",
                //         title: "Type: boolean"
                //     };
                // }

                subSchema.properties[inputName] = {
                // subSchema.items.push({
                    type: "object",
                    title: "Input " + (index+1) + ": " + inputName + (input.required ? ' *' : ''),
                    propertyOrder: index,
                    options: {
                        disable_collapse: true
                    },
                    properties: {
                        value: input,
                        name: { // This is hidden since it should not be modified by user
                            type: "string",
                            default: inputName,
                            options: {
                                hidden: true
                            }
                        }
                    }
                };
            });

            return subSchema;
        }

        var definitions = {};

        // Create the sub-schema for the action inputs
        var actionInputSchema = convertInputToSchema(actionsForApps[parameters.app].actions[parameters.action].args, parameters.action);

        // Create the sub-schema for the flags
        var flags = _.cloneDeep(flagsList);
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
        var filters = _.cloneDeep(filtersList);
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
                    enum: actionsForApps[parameters.app].devices
                },
                action: {
                    type: "string",
                    title: "Action",
                    enum: [parameters.action]
                },
                inputs: _.cloneDeep(actionInputSchema),
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
                    required: ['status'],
                    properties: {
                        name: {
                            type: "string",
                            options: {
                                hidden: true
                            }
                        },
                        status: {
                            type: "string",
                            title: "Status",
                            enum: actionsForApps[parameters.app].actions[parameters.action].returns,
                            default: "Success"
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
                                        // Use a oneOf to include a flag plus its
                                        // inputs in a subschema.
                                        oneOf: _.cloneDeep(oneOfFlags)
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
                                                    // Use a oneOf to include a filter plus its
                                                    // inputs in a subschema.
                                                    oneOf: _.cloneDeep(oneOfFilters)
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
        var x = event.pageX + offsetX;
        var y = event.pageY + offsetY;

        insertNode(app, action, x, y, true);
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
        if (parameters && node.isNode() && this.startNode == parameters.name) {
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
            parameters.name = newNodes[i].data("id");
            parameters.next = [];
            newNodes[i].data("parameters", parameters);
        }
    }

    function transformInputsToLoad(workflowData) {
        _.each(workflowData.steps, function (step) {
            step.inputs = _.reduce(step.inputs, function (result, arg) {
                result[arg.name] = _.clone(arg);
                return result;
            }, {});

            _.each(step.next, function (nextStep) {
                _.each(nextStep.flags, function (flag) {
                    flag.args = _.reduce(flag.args, function (result, arg) {
                        result[arg.name] = _.clone(arg);
                        return result;
                    }, {});
                    
                    _.each(flag.filters, function (filter) {
                        filter.args = _.reduce(filter.args, function (result, arg) {
                            result[arg.name] = _.clone(arg);
                            return result;
                        }, {});
                    })
                })
            });
        });
    }

    function transformInputsToSave(steps) {
        _.each(steps, function (step) {
            step.inputs = _.reduce(step.inputs, function (result, arg) {
                if (typeof arg !== 'object') return result;
                result.push({ name: arg.name, value: arg.value });
                return result;
            }, []);

            _.each(step.next, function (nextStep) {
                _.each(nextStep.flags, function (flag) {
                    flag.args = _.reduce(flag.args, function (result, arg) {
                        if (typeof arg !== 'object') return result;
                        result.push({ name: arg.name, value: arg.value });
                        return result;
                    }, []);
                    
                    _.each(flag.filters, function (filter) {
                        filter.args = _.reduce(filter.args, function (result, arg) {
                            if (typeof arg !== 'object') return result;
                            result.push({ name: arg.name, value: arg.value });
                            return result;
                        }, []);
                    });
                })
            });
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
        $("#currentWorkflowText").text(currentPlaybook + " - " + currentWorkflow);

        var workflowData = function () {
            var tmp = null;
            refreshJwtAjax({
                'async': false,
                'type': "GET",
                'global': false,
                'headers':{"Authorization": 'Bearer ' + authToken},
                'url': "/api/playbooks/" + currentPlaybook + "/workflows/" + currentWorkflow,
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
        cy = cytoscape(this.cyOptions);

        // Enable various Cytoscape extensions
        // Undo/Redo extension
        ur = cy.undoRedo({});

        // Panzoom extension
        cy.panzoom({});

        // Extension for drawing edges
        cy.edgehandles(this.cyEdgehandlesOptions);

        // Extension for copy and paste
        cy.clipboard();

        //Extension for grid and guidelines
        cy.gridGuide({
            // drawGrid: true,
            // strokeStyle: '#222'
            //options...
        });

        transformInputsToLoad(workflowData);

        // Load the data into the graph
        // If a node does not have a label field, set it to
        // the action. The label is what is displayed in the graph.
        var edges = [];
        var steps = workflowData.steps.map(function(value) {
            var ret = { group: "nodes", position: _.clone(value.position) };
            ret.data = { id: value.name, parameters: _.cloneDeep(value), label: value.action };
            setNodeDisplayProperties(ret);
            _.each(value.next, function (nextStep) {
                edges.push({
                    group: "edges",
                    data: {
                        id: value.name + nextStep.name,
                        source: value.name,
                        target: nextStep.name,
                        parameters: _.clone(nextStep)
                    }
                });
            });
            // if (!value.data.hasOwnProperty("label")) {
            //     ret.data.label = value.action;
            // }
            return ret;
        });

        steps = steps.concat(edges);

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

        //Enable our execute button once we load a workflow
        $("#execute-button").removeAttr('disabled');
        $("#clear-execution-highlighting-button").removeAttr('disabled');
    }


    function closeCurrentWorkflow() {
        $("#cy").empty();
        $("#currentWorkflowText").text("");
        hideParameters();
        showInstructions();
    }

    function hideParameters() {
        $("#parametersBar").addClass('hidden');
    }

    // Download list of workflows for display in the Workflows list
    function getPlaybooksWithWorkflows() {

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
                                       _doesWorkflowExist);
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
                                       _doesWorkflowExist);
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
                                       _doesPlaybookExist);
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
                                       _doesPlaybookExist);
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

        refreshJwtAjax({
            'async': true,
            'type': "GET",
            'global': false,
            'headers':{"Authorization": 'Bearer ' + authToken},
            'url': "/api/playbooks",
            'success': function (data) {
                //Destroy the existing tree if necessary
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
                })
                // handle double click on workflow, load workflow graph for editing
                .bind("dblclick.jstree", function (event, data) {

                    var node = $(event.target).closest("li");
                    var node_id = node[0].id; //id of the selected node
                    node = $('#workflows').jstree(true).get_node(node_id);

                    var workflowName = node.text;
                    if (node.data && node.data.playbook) {
                        loadWorkflow(node.data.playbook, workflowName);

                        // hide parameters panel until first click on node
                        hideParameters();

                        //hide our bootstrap modal
                        $('#workflowsModal').modal('hide');
                    }
                });
            },
            'error': function (e) {
                $.notify('Error retrieving playbooks.', 'error');
                console.log(e);
            }
        });
    }

    //-------------------------
    // Configure event handlers
    //-------------------------
    $("#palette ul li a").each(function() {
        $(this).attr("href", location.href.toString()+$(this).attr("href"));
    });

    // Handle drops onto graph
    $( "#cy" ).droppable( {
        drop: handleDropEvent
    } );

    // Handle new button press
    $( "#new-button" ).click(function() {
        // $("#workflows-tab").tab('show');
        showDialog("Create New Workflow",
                   "Playbook Name",
                   "",
                   false,
                   "Workflow Name",
                   "",
                   false,
                   newWorkflow,
                   _doesWorkflowExist);
    });

    // Handle save button press
    $( "#save-button" ).click(function() {
        if (cy === null)
            return;

        if ($(".nav-tabs .active").text() === "Graphical Editor") {
            // If the graphical editor tab is active
            saveWorkflow(currentPlaybook, currentWorkflow, cy.elements().jsons());
        } else {
            // If the JSON tab is active
            saveWorkflowJson(currentPlaybook, currentWorkflow, document.getElementById('cy-json-data').value);
        }
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
    getPlaybooksWithWorkflows();

    // Download all actions in all apps for display in the Actions tree
    refreshJwtAjax({
        'async': true,
        'type': "GET",
        'global': false,
        'headers':{"Authorization": 'Bearer ' + authToken},
        'url': "/api/apps/actions",
        'success': function (data) {
            $('#actions').jstree({
                'core' : {
                    'data' : formatAppsActionJsonDataForJsTree(data)
                }
            })
            //Commented out for now
            // .bind("ready.jstree", function (event, data) {
            //     $(this).jstree("open_all"); // Expand all
            // })
            // handle double click on workflow, add action node to center of canvas
            .bind("dblclick.jstree", function (event, data) {
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


    //---------------------------------
    // Other setup
    //---------------------------------
    showInstructions();

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

    var executionResultsTable = $("#executionResultsTable").DataTable({
        columns:[
            { data: "name", title: "ID" },
            { data: "timestamp", title: "Timestamp" },
            { data: "type", title: "Type" },
            { data: "input", title: "Input" },
            { data: "result", title: "Result" }
        ],
        order: [1, 'desc']
    });

    function handleStreamStepsEvent(data){
        var id = data.name;
        var type = data.type;
        var elem = cy.elements('node[id="' + id + '"]');

        executionResultsTable.row.add(data);
        executionResultsTable.draw();

        // var row = executionDialog.find("table").get(0).insertRow(-1);
        // var id_cell = row.insertCell(0);
        // id_cell.innerHTML = data.name;

        // var type_cell = row.insertCell(1);
        // type_cell.innerHTML = data.type;

        // var input_cell = row.insertCell(2);
        // input_cell.innerHTML = data.input;

        // var result_cell = row.insertCell(3);
        // result_cell.innerHTML = data.result;

        if(type === "SUCCESS"){
            elem.addClass('good-highlighted');
        }
        else if(type === "ERROR"){
            elem.addClass('bad-highlighted');
        }

    }

    window.stepResultsSSE.onmessage = function(message) {
        var data = JSON.parse(message.data);
        handleStreamStepsEvent(data);
    }
    window.stepResultsSSE.onerror = function(e){
        console.log("ERROR");
        console.log(e);
        stepResultsSSE.close();
    }
});
