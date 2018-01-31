$(document).ready(function() {
    $('#video-modal').on('hidden.bs.modal', function () {
        document.getElementById('player').pause();
        document.getElementById('player').currentTime = 0;
    });
});

function setSrc(path) {
    document.getElementById("player").src = path
    document.getElementById("vidtext").innerHTML = document.getElementById(path).innerHTML
}

