

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

    // Download list of workflows for display in the Workflows list
    function getPlaybooksWithWorkflows() {

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

    // Handle drops onto graph
    $( "#cy" ).droppable( {
        drop: handleDropEvent
    } );

    //---------------------------------
    // Setup Workflows and Actions tree
    //---------------------------------

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
});
