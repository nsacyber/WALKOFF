$(document).on("DOMContentLoaded", function(e){
    if (Notification.permission !== "granted"){
        Notification.requestPermission();
    }


});

$(document).ready(function(){
      //Load default page
      $.ajax({
          url:'interface/' + default_page + '/display',
          data:{},
          headers:{"Authentication-Token":authKey},
          type:"POST",
          success: function(e){
              data = e;
              $("#ss_main").html(data);
          },
          error: function(e){
              $("#ss_main").html("<p> Interface could not be Loaded! </p>");
          }
      });
});


