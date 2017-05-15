

$(function() {
//    $("#createUser").hide();
    getRole();
    $currentUser = $("#username option:selected");
    function getUserList(){
        $.ajax({
            url: "/users",
            data: {},
            headers: {"Authentication-Token": authKey},
            type: "GET",
            success: function (e) {
                users = e.substring(2, e.length-2).split(",");
                $("#username .userOption").remove();
                for(i=0;i<users.length;i++){
                    $("#username").append("<option class='userOption' value=" + user[i] +">" + user[i] + "</option>");
                }
            },
            error: function (e) {
                console.log("failed");
            }
        });
    }

    console.log($("#username option:selected").text())
    $.ajax({
            url: "users/" + ($("#username option:selected").text()),
            data: {},
            headers: {"Authentication-Token": authKey},
            type: "GET",
            success: function (e) {
                for (i = 0; i < e['roles'].length; i++) {
                    $('#roles').append('<option value="' + e['roles'][i].name + '">' + e['roles'][i].description + '</option>');
                }
                $('#active').prop("checked",e.active);

            },
            error: function (e) {
                console.log("failed")
                $("#templatesPath").val("Error");
            }
        });

     $("#editUser").click(function(){
//        $("#currentUserInfo").hide();
        $("#updateUserForm #username").val($currentUser['username']);

     });
     $("#submitUpdate").click(function(){
        $.ajax({
            url: 'users/'+$currentUser['username'],
            data: $("#updateUserForm").serialize(),
            headers: {"Authentication-Token": authKey},
            type: "POST",
            success: function (e) {
                alert("user info" + data);
                getUserList();
            },
            error: function (e) {
                console.log('no user info obtained')
            }
        });
     });
    $("#addUser").click(function(){
//        $("#currentUserInfo").hide();
//        $("#createUser").show();
    });
    $("#deleteUser").click(function(){
       user = $("#username option:selected").val();
       if(user != 'admin'){
            $.ajax({
                url: 'users/' + user,
                data: {},
                headers: {"Authentication-Token": authKey},
                type: "DELETE",
                success: function (e) {
                    $("#username option:selected").remove();
                },
                error: function (e) {
                    $("#templatesPath").val("Error");
                }
                });
       }else{
            alert('cannot delete admin user');
       }
    });
});
$("#username").change(function () {
        $.ajax({
            url: "users/" + ($("#username option:selected").text()),
            data: {},
            headers: {"Authentication-Token": authKey},
            type: "GET",
            success: function (e) {
                $currentUser = e;
                for (i = 0; i < e['roles'].length; i++) {
                    $('#roles').append('<option value="' + e['roles'][i].name + '">' + e['roles'][i].description + '</option>');
                }
                $('#active').prop("checked",e.active);

            },
            error: function (e) {
                console.log("failed")
                $("#templatesPath").val("Error");
            }
        });
    });

$("#saveNewUser").click(function(){
    username = $("#addUserForm #username").val();
    $.ajax({
        url: 'users/' + username,
        data: $("#addUserForm").serialize(),
        headers: {"Authentication-Token": authKey},
        type: "PUT",
        success: function (e) {
            data = e;
            alert("new user added" + e);
            if(e['status'] != 'invalid input'){
                $('#username').append('<option class="userOption" value="' + username + '">' + username + '</option>');
            }

            $('#AddUserForm').trigger("reset");
        },
        error: function (e) {
            $("#templatesPath").val("Error");
        }
    });
});

function getRole(user){
    $.ajax({
        url: '/roles',
        data: {},
        headers: {"Authentication-Token": authKey},
        type: "GET",
        success: function (e) {
            data = e;
            $userRoles = data;
//            addRole($("#addUserForm #username").val())
        },
        error: function (e) {
            $("#templatesPath").val("Error");
        }
    });
};

$.ajax({
    url: 'configuration/workflows_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#workflows_path").val(data["workflows_path"]);
    },
    error: function (e) {
        $("#workflows_path").val("Error");
    }
});

$.ajax({
    url: 'configuration/templates_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#templates_path").val(data["templates_path"]);
    },
    error: function (e) {
        $("#templates_path").val("Error");
    }
});

$.ajax({
    url: 'configuration/profile_visualizations_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#profile_visualizations_path").val(data["profile_visualizations_path"]);
    },
    error: function (e) {
        $("#profile_visualizations_path").val("Error");
    }
});

$.ajax({
    url: 'configuration/keywords_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#keywords_path").val(data["keywords_path"]);
    },
    error: function (e) {
        $("#keywords_path").val("Error");
    }
});
$.ajax({
    url: 'configuration/db_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#db_path").val(data["db_path"]);
    },
    error: function (e) {
        $("#db_path").val("Error");
    }
});

$.ajax({
    url: 'configuration/tls_version',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#tls_version").val(data["tls_version"]);
    },
    error: function (e) {
        $("#tls_version").val("Error");
    }
});
$.ajax({
    url: 'configuration/certificate_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#certificate_path").val(data["certificate_path"]);
    },
    error: function (e) {
        $("#certificate_path").val("Error");
    }
});
$.ajax({
    url: 'configuration/https',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#https").val(data["https"]);
    },
    error: function (e) {
        $("#https").val("Error");
    }
});
$.ajax({
    url: 'configuration/private_key_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#private_key_path").val(data["private_key_path"]);
    },
    error: function (e) {
        $("#private_key_path").val("Error");
    }
});

$.ajax({
    url: 'configuration/debug',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#debug").val(data["debug"]);
    },
    error: function (e) {
        $("#debug").val("Error");
    }
});
$.ajax({
    url: 'configuration/default_server',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#default_server").val(data["default_server"]);
    },
    error: function (e) {
        $("#default_server").val("Error");
    }
});
$.ajax({
    url: 'configuration/host',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#host").val(data["host"]);
    },
    error: function (e) {
        $("#host").val("Error");
    }
});
$.ajax({
    url: 'configuration/port',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = e;
        $("#port").val(data["port"]);
    },
    error: function (e) {
        $("#port").val("Error");
    }
});


//    $("#settingsTabs").tabs({
//        beforeLoad: function(e, ui){
//            console.log(ui);
//            ui.ajaxSettings.url = "#" + ui.tab[0].id;
//            console.log(ui.ajaxSettings.url);
//            e.stopImmediatePropagation();
//        }
//    });
    $("#settingsTabs UL LI A").each(function() {
        $(this).attr("href", location.href.toString()+$(this).attr("href"));
    });
    $("#settingsTabs").tabs();

$("#setForm").on("submit", function (e) {
    $.ajax({
        url: 'configuration/set',
        data: $("#setForm").serialize(),
        headers: {"Authentication-Token": authKey},
        type: "POST",
        success: function (e) {
            data = e;
            console.log(data);
        },
        error: function (e) {
            console.log(e);
        }
    });
    e.preventDefault();
});