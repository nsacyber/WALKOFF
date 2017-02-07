$.ajax({
    url:'configuration/dbPath',
    data:{},
    headers:{"Authentication-Token":authKey},
    type:"POST",
    success: function(e){
        data = JSON.parse(e);
        $("#dbPath").val(data["dbPath"]);
    },
    error: function(e){
        $("#dbPath").val("Error");
    }
});