"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var user_1 = require("./user");
var WorkingUser = (function () {
    function WorkingUser() {
        this.roles = [];
        this.role_ids = [];
    }
    WorkingUser.toUser = function (workingUser) {
        var returnUser = new user_1.User();
        returnUser.id = workingUser.id;
        returnUser.username = workingUser.username;
        returnUser.roles = workingUser.roles;
        returnUser.role_ids = workingUser.role_ids;
        returnUser.active = workingUser.active;
        returnUser.old_password = workingUser.currentPassword;
        returnUser.password = workingUser.newPassword;
        return returnUser;
    };
    return WorkingUser;
}());
exports.WorkingUser = WorkingUser;
