$(document).on("DOMContentLoaded", function(e){
    if (Notification.permission !== "granted"){
        Notification.requestPermission();
    }
});

console.log(default_page)
core.start("systemPage", {
    options: {page: default_page}
});



