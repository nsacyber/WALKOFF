content = $(".contentContainer > iframe");

function changeInterface(page_url, opt){
    try{

        var module = function(){
            var tmp = null;
              $.ajax({
                  url:page_url,
                  data:opt.data || {},
                  type:"POST",
                  async:false,
                  dataType:"html",
                  beforeSend: function(xhr, settings){
                        xhr.setRequestHeader("Authentication-Token", authKey);
                  },
                  success: function(data){
                      //$(content).contents().find('html').html(data);
                      var position = data.search("<head>");
                      var insertion = $("#globalVariables").prop("outerHTML");
                      data = [data.slice(0, position), insertion, data.slice(position)].join('');

//                      var position2 = data.search("<body>");
//                      var insertion2 = `<script> (function (){ $(document).bind({
//                       beforeunload: function(e){ e.preventDefault(); },
//                       unload: function(e){ e.preventDefault(); }
//                       });}());</script>`
//                      data = [data.slice(0, position2), insertion2, data.slice(position2)].join('');


                      $(content).attr("srcdoc", data);
                  },
                  error: function(e){
                      //$(content).attr("src", "data:text/html;charset=utf-8," + escape(data));
                  }
              });
            return tmp;
          }();
    }catch(e){
        console.log("ERROR");
        console.log(e);
        module = null;
    }
}

var sandbox = function(core, instanceId, options, moduleId){
    this.myProperty = "bar";
    core._mediator.installTo(this);
    this.myEmit = function(channel, data){
        core.emit(channel + '/' + instanceId, data);
    }
    this.id =instanceId;
    return this;
};

core = new scaleApp.Core(sandbox);

systemPage = function(sandbox){
    return{
        init: function(opt){
             //Load default page
            page_url = (opt.preface || 'interface') + '/' + opt.page + '/display';
            changeInterface(page_url, opt);
        },
        destroy: function(){
            //$(".contentContainer > iframe")[0].contentWindow.location.reload();
            //$(".contentContainer > iframe").attr("srcdoc", "");

        }
    };
};

core.register("systemPage", systemPage);
core.start("systemPage", {
    options: {page: default_page}
});

