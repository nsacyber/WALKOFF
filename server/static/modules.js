var sandbox = function(core, instanceId, options, moduleId){
    this.myProperty = "bar";
    core._mediator.installTo(this);
    this.myEmit = function(channel, data){
        core.emit(channel + '/' + instanceId, data);
    }
    this.id =instanceId;
    return this;
};

var core = new scaleApp.Core(sandbox);

var systemPage = function(sandbox){
    return{
        init: function(opt){
              //Load default page
             module = function(){
                var tmp = null;
                  $.ajax({
                      url:'interface/' + opt.page + '/display',
                      data:{},
                      headers:{"Authentication-Token":authKey},
                      type:"POST",
                      'async':false,
                      success: function(e){
                          tmp = e;
                          //$("#ss_main").html(data);
                      },
                      error: function(e){
                          $("#ss_main").html("<p> Interface could not be Loaded! </p>");
                      }
                  });

                return tmp;
              }();
              $("#ss_main").html(module);

        },
        destroy: function(){
            $("#ss_main").empty();
            module = null;
        }
    };
};

core.register("systemPage", systemPage);