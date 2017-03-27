function displayNameList(devices){
    for(device in devices){
        if(devices[device]["name"] != undefined){
            vsly.add("<li>" + devices[device]["name"] + "</li>");
        }
    }
}
$(function() {
    console.log("this main does not run");
});

for(var app in apps){
    $("#appList").append("<li>" + apps[app] + "</li>");
}

//
// HORIZONTAL ITEM
//

(function () {
    var $vframe  = $('#smart');
    var $slidee = $vframe.children('ul').eq(0);
    var $vwrap   = $vframe.parent();

    // Call Sly on frame
    vsly = new Sly($('#smart'), {
        itemNav: 'basic',
        smart: 1,
        activateOn: 'click',
        mouseDragging: 1,
        touchDragging: 1,
        releaseSwing: 1,
        startAt: 3,
        scrollBar: $vwrap.find('.scrollbar'),
        scrollBy: 1,
        pagesBar: $vwrap.find('.pages'),
        activatePageOn: 'click',
        speed: 300,
        elasticBounds: 1,
        easing: 'easeOutExpo',
        dragHandle: 1,
        dynamicHandle: 1,
        clickBar: 1,
    }).init();

    // Add item
    $vwrap.find('.add').on('click', function () {
        var defaultValues = {"name":apps[sly.rel.activeItem] + "-" + $slidee.children().length, "app":apps[sly.rel.activeItem], "ipaddr":"", "port":0, "username":"", "pw":""};
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
            url:'/configuration/' + apps[sly.rel.activeItem] + '/devices/add',
            data:$("#deviceForm").serialize(),
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success:function(e){
                console.log(e);
                $vframe.sly('add', '<li>' + defaultValues["name"] + '</li>');
                vsly.toEnd();

            },
            error: function(e){
                console.log("ERROR");
            }
        });
    });

    // Remove item
    $vwrap.find('.remove').on('click', function () {

        $.ajax({
            url:'/configuration/' + apps[sly.rel.activeItem] + '/devices/' + vsly.items[vsly.rel.activeItem].el.innerHTML + '/remove',
            data:{},
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success:function(e){
                console.log(e);
                $vframe.sly('remove', vsly.rel.activeItem);
            },
            error: function(e){
                console.log("ERROR");
            }
        });
    });


    var $frame = $('#centered');
    var $wrap  = $frame.parent();

    // Call Sly on frame
   sly = new Sly($("#centered"),{
        horizontal: 1,
        itemNav: 'centered',
        smart: 1,
        activateOn: 'click',
        mouseDragging: 1,
        touchDragging: 1,
        releaseSwing: 1,
        startAt: 4,
        scrollBar: $wrap.find('.scrollbar'),
        scrollBy: 1,
        speed: 300,
        elasticBounds: 1,
        easing: 'easeOutExpo',
        dragHandle: 1,
        dynamicHandle: 1,
        clickBar: 1,

        // Buttons
        prev: $wrap.find('.prev'),
        next: $wrap.find('.next')
    }).init();

     $.ajax({
        url:'/configuration/' + apps[sly.rel.activeItem] + '/devices/all',
        data:{},
        headers:{"Authentication-Token":authKey},
        type:"POST",
        success: function(e){
            displayNameList(JSON.parse(e));
            vsly.reload();
        },
        error: function(e){
            console.log("ERRROR");
        }
    });


    sly.on('active', function(eventName, itemIndex){
        $('#deviceForm').find("input[type=text], input[type=password]").val("");
        vsly.destroy().init();
        var app = apps[itemIndex];
        $("#deviceList").empty();
        $.ajax({
            url:'/configuration/' + app + '/devices/all',
            data:{},
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success: function(e){
                displayNameList(JSON.parse(e));
                vsly.reload();
            },
            error: function(e){
                console.log("ERRROR");
            }
        });
    });

    vsly.on('active', function(eventName, itemIndex){
        $(this).closest('#deviceForm').find("input[type=text]").val("");
        $.ajax({
            url:'/configuration/' + apps[sly.rel.activeItem] + '/devices/' + vsly.items[itemIndex].el.innerHTML + '/display',
            data:{},
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success:function(e){
                values = JSON.parse(e);
                console.log(values);
                for(key in values){
                    if(key == "ip"){
                        k = "ipaddr";
                    }else if(key == "password"){
                        k = "pw";
                    }
                    else{
                        k = key;
                    }
                    $("#" + k).val(values[key]);
                }
            },
            error: function(e){
                console.log("ERROR");
            }
        });
    });

    $( "#deviceForm" ).submit(function(event){
          event.preventDefault();
         $.ajax({
            url:'/configuration/' + apps[sly.rel.activeItem] + '/devices/' + vsly.items[vsly.rel.activeItem].el.innerHTML + '/edit',
            data:$("#deviceForm").serialize(),
            headers:{"Authentication-Token":authKey},
            type:"POST",
            success:function(e){
                console.log(e);
                var data = JSON.parse(e);
                if(!("status" in data && data["status"] == "device could not be edited")){
                    vsly.items[vsly.rel.activeItem].el.innerHTML = $("#name")[0].value;
                }

            },
            error: function(e){
                console.log("ERROR");
            }
        });
     });
}());








