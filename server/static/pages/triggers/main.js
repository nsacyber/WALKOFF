(function () {
    triggerData = [];
    params = {};
    //Get List of flags
     $.ajax({
            url: "/flags",
            data: {},
            headers: {"Authentication-Token": authKey},
            type: "GET",
            success: function (e) {
//               console.log(JSON.parse(e));
               parameters = JSON.parse(e);
            },
            error: function (e) {
                console.log("failed")
                $("#templatesPath").val("Error");
            }
        });


    //Get and display the list of triggers
    function getTriggerList(){
        $.ajax({
            url:'/execution/listener/triggers',
            headers:{"Authentication-Token":authKey},
            type:"GET",
            success:function(data){
                result = JSON.parse(data);
                triggers = result['triggers'];
                $("#trigger .triggerOption").remove();
                for(i=0;i<triggers.length;i++){
                    trigger=triggers['' +i +""];
                    $("#trigger").append("<option value="+ i  + " class='triggerOption'>"+ trigger['name'] + "</option>");
                }
                triggerData = result;
            },
            error: function(e){
                console.log("ERROR");
            }
        });
    };
    getTriggerList();


//    $("#parameterEdit").hide();
    var $slidee = $("#smart").children('ul').eq(0);

    // Add item
    $("#trigger").on("change",function(){
        val = $("#trigger option:selected").val();
        index = $("#trigger option:selected").val();
        trigger = triggerData['triggers'][''+ val +''];
        $(".workflow").empty().append('<div>' + trigger['workflow'] + '</div>');
        $(".playbook").empty().append('<div>' + trigger['playbook'] + '</div>');

    });
    function createSchema(parameters) {
        var appNames = [];
        var appActions = {};
        $.each(appData, function( appName, actions ) {
            appNames.push(appName);
            appActions[appName] = [];
            $.each(actions, function( actionName, actionProperties ) {
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



        schema.properties.next = {
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
        };


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

    // Initialize the editor with a JSON schema
//    console.log(parameters)
    parameters = transformParametersToSchema(parameters);
   console.log(parameters);

    $('#addTrigger').on('click', function () {
        name = $('#deviceForm #name').val();
        $.ajax({
        url: 'execution/listener/triggers/' + name + '/add',
        data: $("#deviceForm").serialize(),
        headers: {"Authentication-Token": authKey},
        type: "POST",
        success: function (data) {
            console.log('trigger add success');
            getTriggerList();
            $("#deviceForm").trigger("reset");

        },
        error: function (e) {
            console.log('trigger add failed');
            console.log(e);
        }
    });

    });

    //Show edit dialog
    $("#editTrigger").on('click',function(){
        index = $("#trigger option:selected").val();
        trigger = triggerData['triggers'][''+index];
        if($("#trigger option:selected").attr('value') == 'none'){
            alert("Select a trigger");
        }else{
//            $("#parameterEdit").show();
            $("#name").val(trigger['name']);
            $("#playbook").val(trigger['playbook']);
            $("#workflow").val(trigger['workflow']);
            $("#conditional").val(trigger['conditional']);
        };

    });
    //Edit item
    $("#editformSubmit").on('click',function(){
        if($("#trigger option:selected").attr('value') == 'none'){
            alert("Select a trigger");
        }else{
            name = $("#trigger option:selected").text();
             $.ajax({
            url:'execution/listener/triggers/'+ name + '/edit' ,
            data: $("#editDeviceForm").serialize(),
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success:function(e){
                //refresh the list of triggers
                getTriggerList();
                $("#editDeviceForm").trigger("reset");
            },
            error: function(e){
                console.log("ERROR");
            }
        });
        };
    })
    // Remove item
    $('.remove').on('click', function () {
        if($("#trigger option:selected").attr('value') == 'none'){
            alert("Select a trigger");
        }else{
            name = $("#trigger option:selected").text();
             $.ajax({
            url:'execution/listener/triggers/'+ name + '/remove' ,
            data:{},
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success:function(e){
                // refresh the list of triggers
                $("#trigger option(1)").prop('sl')
                getTriggerList();
            },
            error: function(e){
                console.log("ERROR");
            }
        });
        };
    });



}());
