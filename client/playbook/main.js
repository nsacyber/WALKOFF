if (typeof(EventSource) !== "undefined") {
    stepResultsSSE = new EventSource('workflowresults/stream-steps');

}
else {
    console.log('EventSource is not supported on your browser. Please switch to a browser that supports EventSource to receive real-time updates.');
}


$(function(){
    "use strict";

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
    var authKey = localStorage.getItem('authKey');

    //--------------------
    // Top level functions
    //--------------------

    // Reformat the JSON data returned from the /playbook endpoint
    // into a format that jsTree can understand.
    function formatWorkflowJsonDataForJsTree(data) {
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


    // Reformat the JSON data returned from the /api/apps/actions endpoint
    // into a format that jsTree can understand.
    function formatAppsActionJsonDataForJsTree(data) {
        appData = {};
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
                // type: "array",
                title: "Inputs",
                required: ['$action'],
                options: {
                    hidden: args.length === 0,
                    // disable_array_add: true,
                    // disable_array_delete: true,
                    // disable_array_reorder: true
                },
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

                input.title = "Type: " + input.type;

                //Hack: allow for output references "@<step_name>" for number fields
                if (input.type === "number" || input.type === "integer") input.type = "string";

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
        var actionInputSchema = convertInputToSchema(appData[parameters.app].actions[parameters.action].args, parameters.action);

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
                    enum: appData[parameters.app].devices
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
                            enum: appData[parameters.app].actions[parameters.action].returns,
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

    // Modify the parameters JSON object a little to conform to the schema expected by the parameters form
    function transformParametersToSchema(parameters) {
        parameters = _.cloneDeep(parameters);

        // We need to store a hidden property since in an oneOf,
        // the schema must match exactly one of the options. There
        // can be cases where two actions contain the exact same arguments,
        // so to distinguish the two actions place the action name in
        // in the $action property. This action is hidden and cannot be
        // modified by the user.
        // parameters.$action = parameters.action;

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
    function transformParametersFromSchema(_parameters) {
        var parameters =  _.cloneDeep(_parameters);

        // parameters.action = parameters.$action;
        // delete parameters.input.$action;

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
        editor.getEditor('root.action').disable();
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

            ele.data('parameters', updatedParameters);
            // ele.data('label', updatedParameters.action);
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
                name: inputInfo.name,
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
                    inputs: inputs,
                    name: id.toString(),
                    next: [],
                }
            },
        };

        setNodeDisplayProperties(nodeToBeAdded);

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
            'url': "/api/playbooks/" + oldPlaybookName,
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
            'url': "/api/playbooks/" + oldPlaybookName + "/copy",
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
            'url': "/api/playbooks/" + playbookName,
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
            'url': "/api/playbooks/" + playbookName + "/workflows/" + oldWorkflowName,
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
            'url': "/api/playbooks/" + playbookName + "/workflows/" + oldWorkflowName + "/copy",
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
            'url': "/api/playbooks/" + playbookName + "/workflows/" + workflowName,
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
            'dataType': 'json',
            'data': JSON.stringify({name: workflowName}),
            'contentType': 'application/json; charset=utf-8',
            'url': "/api/playbooks/" + playbookName + "/workflows",
            'success': function (data) {
                downloadWorkflowList();

                //If nothing is currently loaded, load our new workflow.
                if (!cy) loadWorkflow(playbookName, workflowName);

                $.notify('Workflow ' + workflowName + ' added successfully.', 'success');
            },
            'error': function (e) {
                $.notify('Workflow ' + workflowName + ' could not be added.', 'error');
                console.log(e);
            }
        });
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

    function saveWorkflow(playbookName, workflowName, _workflowData) {
        if (!startNode) {
            $.notify('Workflow cannot be saved without a starting step.', 'warning');
            return;
        }
        var workflowData = _.filter(_workflowData, function (data) { return data.group === "nodes"; });

        var steps = _.map(workflowData, function (step) {
            var ret = _.cloneDeep(step.data.parameters);
            ret.position = _.clone(step.position);
            return ret;
        });
        transformInputsToSave(steps);
        var data = JSON.stringify({start: startNode, steps: steps });
        $.ajax({
            'async': false,
            'type': "POST",
            'global': false,
            'dataType': 'json',
            'contentType': 'application/json; charset=utf-8',
            'headers':{"Authentication-Token":authKey},
            'url': "/api/playbooks/" + playbookName + "/workflows/" + workflowName + "/save",
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

    function setNodeDisplayProperties(step) {
        //add a type field to handle node styling
        var app = appData[step.data.parameters.app];
        var action = app.actions[step.data.parameters.action];

        if (action.event) {
            step.data.type = 'eventAction';

            // step.data.label += ' (' + action.event + ')';
        }
        else {
            step.data.type = 'action';
        }
    }

    function loadWorkflow(playbookName, workflowName) {

        currentPlaybook = playbookName;
        currentWorkflow = workflowName;
        $("#currentWorkflowText").text(currentPlaybook + " - " + currentWorkflow);

        var workflowData = function () {
            var tmp = null;
            $.ajax({
                'async': false,
                'type': "GET",
                'global': false,
                'headers':{"Authentication-Token":authKey},
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
        cy = cytoscape({
            container: document.getElementById('cy'),

            boxSelectionEnabled: false,
            autounselectify: false,
            wheelSensitivity: 0.1,
            layout: { name: 'preset' },
            style: [
                {
                    selector: 'node[type="action"]',
                    css: {
                        'content': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'shape': 'roundrectangle',
                        'background-color': '#bbb',
                        'selection-box-color': 'red',
                        'font-family': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif, sans-serif',
                        'font-weight': 'lighter',
                        'font-size': '15px',
                        'width':'40',
                        'height':'40'
                    }
                },
                {
                    selector: 'node[type="eventAction"]',
                    css: {
                        'content': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'shape': 'star',
                        'background-color': '#edbd21',
                        'selection-box-color': 'red',
                        'font-family': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif, sans-serif',
                        'font-weight': 'lighter',
                        'font-style': 'italic',
                        'font-size': '15px',
                        'width':'40',
                        'height':'40'
                    }
                },
                {
                    selector: 'node:selected',
                    css: {
                        'background-color': '#45F'
                    }
                },
                {
                    selector: '.good-highlighted',
                    css: {
                        'background-color': '#399645',
                        'transition-property': 'background-color',
                        'transition-duration': '0.5s'
                    }
                },
                {
                    selector: '.bad-highlighted',
                    css: {
                        'background-color': '#8e3530',
                        'transition-property': 'background-color',
                        'transition-duration': '0.5s'
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
                        'text-halign': 'center'
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
                        status: 'Success',
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
        $("execute-button").removeAttr('disabled');
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
        // $("#workflows-tab").tab('show');
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

    $( "#execute-button" ).click(function() {
        window.executionDialog = $("#executionModal").clone().removeClass('hidden');
        executionDialog.dialog({
            autoOpen: false,
            modal: false,
            title: "Execution Results",
            width: 600,
            close: function(event, ui){
                cy.elements().removeClass("good-highlighted bad-highlighted");
            }
        });

        executionDialog.dialog( "open" );

        $(executionDialog).find("button").on("click", function(){
            cy.elements().removeClass("good-highlighted bad-highlighted");
            executionDialog.dialog("close");
        });
        $.ajax({
            'async': true,
            'type': "POST",
            'global': false,
            'headers':{"Authentication-Token":authKey},
            'url': "/api/playbooks/" + currentPlaybook + "/workflows/" + currentWorkflow + "/execute",
            'success': function (data) {
                console.log(currentWorkflow + ' is scheduled to execute.', 'success');
                //Set up event listener for workflow results if possible
            },
            'error': function (jqXHR, status, error) {
                console.log(currentWorkflow + ' has failed to be scheduled.', 'error');
                //$("#eventList").append("<li>" + currentWorkflow + " has failed to be scheduled.</li>");
            }
        });
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

            // Now is a good time to download all devices for all apps
            _.each(appData, function(actions, appName) {
                $.ajax({
                    'async': false,
                    'type': "GET",
                    'global': false,
                    'headers':{"Authentication-Token":authKey},
                    'url': "/api/apps/" + appName + "/devices",
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
        'url': "/api/flags",
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
        'url': "/api/filters",
        'dataType': 'json',
        'success': function (data) {
            filtersList = data.filters;
        }
    });

    //---------------------------------
    // Other setup
    //---------------------------------
    showInstruction();

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

    function handleStreamStepsEvent(data){
        var id = data.name;
        var type = data.type;
        var elem = cy.elements('node[id="' + id + '"]');

        var row = executionDialog.find("table").get(0).insertRow(-1);
        var id_cell = row.insertCell(0);
        id_cell.innerHTML = data.name;

        var type_cell = row.insertCell(1);
        type_cell.innerHTML = data.type;

        var input_cell = row.insertCell(2);
        input_cell.innerHTML = data.input;

        var result_cell = row.insertCell(3);
        result_cell.innerHTML = data.result;

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
