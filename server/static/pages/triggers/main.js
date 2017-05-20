(function () {
    triggerData = [];
    params = {};
    var flagsList = [];
    var filtersList = [];
    var triggerEditor = null;

    $("#editformSubmit").prop("disabled",true);
    $("#editTrigger").prop("disabled",true);
    $(".remove").prop("disabled",true);

    //Get List of flags
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

    // Get list of all filters
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

    //Get and display the list of triggers
    function getTriggerList(){
        $.ajax({
            url:'/execution/listener/triggers',
            headers:{"Authentication-Token":authKey},
            type:"GET",
            success:function(data){
                result = data;
                triggers = result['triggers'];
                $("#triggerList .triggerOption").remove();
                for(i=0;i<triggers.length;i++){
                    trigger=triggers['' +i +""];
                    $("#triggerList").append("<option value="+ i  + " class='triggerOption'>"+ trigger['name'] + "</option>");
                }
                triggerData = result;
            },
            error: function(e){
                console.log("ERROR");
            }
        });
    };
    getTriggerList();


    var $slidee = $("#smart").children('ul').eq(0);

    // Add item
    $("#triggerList").on("change",function(){
        $("#editTrigger").prop("disabled",false);
        $(".remove").prop("disabled",false);
        val = $("#triggerList option:selected").val();
        index = $("#triggerList option:selected").val();
        trigger = triggerData['triggers'][''+ val +''];
        $(".workflow").empty().append('<div>' + trigger['workflow'] + '</div>');
        $(".playbook").empty().append('<div>' + trigger['playbook'] + '</div>');
        $(".conditional").empty().append('<div>' + JSON.stringify(trigger['conditions']) + '</div>');

    });

    function createSchema() {

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
            title: "Trigger Parameters",
            options: {
                disable_collapse: true
            },
            properties: {
                name: {
                    type: "string",
                    title: "Name",
                },
                playbook: {
                    type: "string",
                    title: "Playbook",
                },
                workflow: {
                    type: "string",
                    title: "Workflow",
                },
                conditional: {
                    type: "array",
                    headerTemplate: "Conditionals",
                    items: {
                        type: "object",
                        title: "Next Conditional",
                        headerTemplate: "Conditional {{ i1 }}",
                        properties: {
                            action: {
                                type: "string",
                                title: "Select Conditional",
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
        };

        return schema;
    }

    function deepcopy(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    // Initialize the editor with a JSON schema. Note that the form
    // element is hidden. It is only used to simplify uploading the
    // form to the server by transferring the data from the JSON
    // editor to the hidden form and then serializing the form data.
    function initAddTriggerForm() {
        var schema = createSchema();
        JSONEditor.defaults.options.theme = 'bootstrap3';
        JSONEditor.defaults.options.iconlib = "bootstrap3";
        triggerEditor = new JSONEditor(document.getElementById('conditionalParameters'),{
            schema: schema,
            startval: {},
            disable_edit_json: true,
            disable_properties: true,
            no_additional_properties: true,
            required_by_default: true
        });
    }

    function resetTriggerEditor() {
        triggerEditor.setValue({});
        $("#editformSubmit").prop("disabled",true);
    }


    $(document).ready(function() {

        initAddTriggerForm();

        $('#addTrigger').on('click', function () {

            // Transfer the data from the JSON editor to the hidden form.
            // This makes it easier to serialize.
            var values = triggerEditor.getValue()
            $("#name").val(values.name);
            $("#playbook").val(values.playbook);
            $("#workflow").val(values.workflow);
            $("#conditional").val(JSON.stringify(values.conditional));

            $.ajax({
                url: 'execution/listener/triggers/' + values.name,
                data: $("#triggerForm").serialize(),
                headers: {"Authentication-Token": authKey},
                type: "PUT",
                success: function (data) {
                    console.log('trigger add success');
                    getTriggerList();
                    resetTriggerEditor();
                },
                error: function (e) {
                    console.log('trigger add failed');
                    console.log(e);
                }
            });

        });

        //Show edit dialog
        $("#editTrigger").on('click',function(){
            index = $("#triggerList option:selected").val();
            $("#editformSubmit").prop("disabled",false);
            trigger = triggerData['triggers'][''+index];
            if($("#triggerList option:selected").attr('value') == 'none'){
            }else{
                triggerEditor.setValue({
                    name: trigger['name'],
                    playbook: trigger['playbook'],
                    workflow: trigger['workflow'],
                    conditional: trigger['conditions']
                });
            };
        });

        //Edit item
        $("#editformSubmit").on('click',function(){
            if($("#triggerList option:selected").attr('value') == 'none'){
                alert("Select a trigger");
            }else{
                var name = $("#triggerList option:selected").text();

                // Transfer the data from the JSON editor to the hidden form.
                // This makes it easier to serialize.
                var values = triggerEditor.getValue()

                // Only send a name over if the user changed it. If
                // not, leave it blank since then an error will occur.
                if (name !== values.name)
                    $("#name").val(values.name);
                else
                    $("#name").val("");
                $("#playbook").val(values.playbook);
                $("#workflow").val(values.workflow);
                $("#conditional").val(JSON.stringify(values.conditional));

                $.ajax({
                    url:'execution/listener/triggers/' + name ,
                    data: $("#triggerForm").serialize(),
                    headers:{"Authentication-Token":authKey},
                    type:"POST",
                    success:function(e){
                        //refresh the list of triggers
                        getTriggerList();
                        resetTriggerEditor();
                    },
                    error: function(e){
                        console.log("ERROR");
                    }
                });
            };
        })

        // Remove item
        $('.remove').on('click', function () {
            if($("#triggerList option:selected").attr('value') == 'none'){
                alert("Select a trigger");
            }else{
                name = $("#triggerList option:selected").text();
                 $.ajax({
                url:'execution/listener/triggers/'+ name,
                data:{},
                headers:{"Authentication-Token":authKey},
                type:"DELETE",
                success:function(e){
                    // refresh the list of triggers
                    $("#triggerList option:selected").remove()
                    getTriggerList();
                },
                error: function(e){
                    console.log("ERROR");
                }
            });
            };
        });
    });


}());
