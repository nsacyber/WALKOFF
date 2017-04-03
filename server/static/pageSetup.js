$(document).on("DOMContentLoaded", function(e){
    if (Notification.permission !== "granted"){
        Notification.requestPermission();
    }
});

core.start("systemPage", {
    options: {page: default_page}
});



