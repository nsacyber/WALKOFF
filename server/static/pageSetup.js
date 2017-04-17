$(document).on("DOMContentLoaded", function(e){
    if (Notification.permission !== "granted"){
        Notification.requestPermission();
    }
});





