function displayNameList(devices){
    for(device in devices){
        console.log(devices[device]);
        if(devices[device]["name"] != undefined){
            vsly.add("<li>" + devices[device]["name"] + "</li>");
        }
    }
}

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

    displayNameList(triggers);

    // Add item
    $vwrap.find('.add').on('click', function () {
        var defaultValues = {"name":triggers[vsly.rel.activeItem] + "-" + $slidee.children().length, "play":"", "conditions":[]};
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

}());








