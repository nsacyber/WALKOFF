(function () {
    triggerData = [];
    //select default elment in the list
    $.ajax({
            url:'/execution/listener/triggers',
            headers:{"Authentication-Token":authKey},
            type:"GET",
            success:function(data){
                console.log('success getting triggers');
                result = JSON.parse(data);
                console.log(result);
                for(i=0;i<result.length;i++){
                    $("#trigger").append("<option value="+ i  + ">"+ result[i]['name'] + "</option>");
                }
                triggerData = result;
            },
            error: function(e){
                console.log("ERROR");
            }
        });

    $("#parameterEdit").hide();
    var $slidee = $("#smart").children('ul').eq(0);

    // Add item
    $("#trigger").on("change",function(){
        val = $("#trigger option:selected").val();
        index = $("#trigger option:selected").val();
        $("#workflow").empty().append('<div>' + triggerData[val]['play'] + '</div>');
        conditionals = JSON.parse(triggerData[val]['conditions']);
        if(conditionals.length === 0 ){
            $("#conditional").empty().append('<p>No conditionsals</p>');
        }else{
            for(i=0;i<conditionals.length;i++){
                $("#conditional").empty().append('<p>' +conditionals[i] +'</p>');
            };
        };
    });

    $('.add').on('click', function () {
        err = {"name":""+ $slidee.children().length, "play":"", "conditions":[]};
        console.log(err);
        console.log("getting ready to add triggers");
        var defaultValues = {"name":"trigger" + "-" + $slidee.children().length, "play":"", "conditions":[]};
        $(this).closest('#deviceForm').find("input[type=text]").val("");
        for(key in defaultValues){
            if(key == "ip"){
                k = "ipaddr";
            }else if(key == "password"){
                k = "pw";
            }
            else{
                k = key;
            }
            $("#" + k).val(defaultValues[key]);
        }

        $.ajax({
        url: 'execution/listener/triggers/add',
        data: $("#deviceForm").serialize(),
        headers: {"Authentication-Token": authKey},
        type: "POST",
        success: function (data) {
            console.log('trigger add success');
            console.log(data);
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
        if($("#trigger option:selected").attr('value') == 'none'){
            alert("Select a trigger");
        }else{
            $("#parameterEdit").show();
            $("#name").val(triggerData[index]['name']);
            $("#play").val(triggerData[index]['play']);
            $("#conditional").val(triggerData[index]['conditional']);
        };

    });
    //Edit item
    $("#editformSubmit").on('click',function(){
        if($("#trigger option:selected").attr('value') == 'none'){
            alert("Select a trigger");
        }else{
        console.log('editdeviceform')
        console.log($("#editDeviceForm").serialize());
            name = $("#trigger option:selected").text();
             $.ajax({
            url:'execution/listener/triggers/'+ name + '/edit' ,
            data: $("#editDeviceForm").serialize(),
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success:function(e){
                console.log(e);
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
                console.log(e);
            },
            error: function(e){
                console.log("ERROR");
            }
        });
        };
    });

}());
