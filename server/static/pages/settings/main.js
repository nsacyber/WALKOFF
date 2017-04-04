// $.ajax({
//     url: '/users',
//     headers: {"Authentication-Token": authKey},
//     type: "POST",
//     success: function (e) {
//         for (var x = 0; x < e.length; x++) {
//             $("#userList").append("<option value='" + x + "'>" + x + "</option>");
//         }
//     },
//     error: function (e) {
//         console.log(e);
//     }
// });

$(function() {
    $("#createUser").hide();

    $.ajax({
            url: "users/" + ($("#username option:selected").text() + "/display"),
            data: {},
            headers: {"Authentication-Token": authKey},
            type: "POST",
            success: function (e) {
                e = JSON.parse(e);
                for (i = 0; i < e['roles'].length; i++) {
                    $('#roles').append('<option value="' + e['roles'][i].name + '">' + e['roles'][i].description + '</option>');
                    $('#password').val("admin");
                    $('#email').val("test@email.com");
                }
                $('#active').prop("checked",e.active);

            },
            error: function (e) {
                console.log("failed")
                $("#templatesPath").val("Error");
            }
        });

     $("#editUser").click(function(){
        $("#currentUserInfo").hide();
        $("#updateUserForm #username").val($currentUser['username']);
     });
    $("#addUser").click(function(){
        $("#currentUserInfo").hide();
        $("#createUser").show();
    });
    $("#deleteUser").click(function(){
       user = $("#username option:selected").val();
       if(user != 'admin'){
            $.ajax({
                url: 'users/' + user + '/remove',
                data: {},
                headers: {"Authentication-Token": authKey},
                type: "POST",
                success: function (e) {
                    data = JSON.parse(e);
                    alert("user removed");
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
$("#username")
    .change(function () {
        $.ajax({
            url: "users/" + ($("#username option:selected").text() + "/display"),
            data: {},
            headers: {"Authentication-Token": authKey},
            type: "POST",
            success: function (e) {
                e = JSON.parse(e);
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
    $.ajax({
        url: 'users/add',
        data: $("#addUserForm").serialize(),
        headers: {"Authentication-Token": authKey},
        type: "POST",
        success: function (e) {
            data = JSON.parse(e);
            alert("new user added" + e);
            $("#currentUserInfo").show();
            $("#createUser").hide();
            addRole($("#addUserForm #username").val())
        },
        error: function (e) {
            $("#templatesPath").val("Error");
        }
    });
});
function addRole(user){
    $.ajax({
        url: 'roles/user/add',
        data: $("#addUserForm").serialize(),
        headers: {"Authentication-Token": authKey},
        type: "POST",
        success: function (e) {
            data = JSON.parse(e);
            alert("new user added" + e);
            $("#currentUserInfo").show();
            $("#createUser").hide();
//            addRole($("#addUserForm #username").val())
        },
        error: function (e) {
            $("#templatesPath").val("Error");
        }
    });
};

$.ajax({
    url: 'configuration/templates_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = JSON.parse(e);
        $("#templates_path").val(data["templates_path"]);
    },
    error: function (e) {
        $("#templates_path").val("Error");
    }
});

$.ajax({
    url: 'configuration/workflows_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = JSON.parse(e);
        $("#workflows_path").val(data["workflows_path"]);
    },
    error: function (e) {
        $("#workflows_path").val("Error");
    }
});
$.ajax({
    url: 'configuration/profile_visualizations_path',
    data: {},
    headers: {"Authentication-Token": authKey},
    type: "GET",
    success: function (e) {
        data = JSON.parse(e);
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
        data = JSON.parse(e);
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
        data = JSON.parse(e);
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
        data = JSON.parse(e);
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
        data = JSON.parse(e);
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
        data = JSON.parse(e);
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
        data = JSON.parse(e);
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
        data = JSON.parse(e);
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
        data = JSON.parse(e);
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
        data = JSON.parse(e);
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
        data = JSON.parse(e);
        $("#port").val(data["port"]);
    },
    error: function (e) {
        $("#port").val("Error");
    }
});

$(function () {
    $("#settingsTabs").tabs();
});

$("#setForm").on("submit", function (e) {
    $.ajax({
        url: 'configuration/set',
        data: $("#setForm").serialize(),
        headers: {"Authentication-Token": authKey},
        type: "POST",
        success: function (e) {
            data = JSON.parse(e);
            console.log(data);
        },
        error: function (e) {
            console.log(e);
        }
    });
    e.preventDefault();
});