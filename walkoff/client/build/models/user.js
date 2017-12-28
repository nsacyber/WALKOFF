"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var workingUser_1 = require("./workingUser");
var User = (function () {
    function User() {
        this.roles = [];
        this.role_ids = [];
    }
    User.toWorkingUser = function (user) {
        var returnUser = new workingUser_1.WorkingUser();
        returnUser.id = user.id;
        returnUser.username = user.username;
        returnUser.roles = user.roles;
        returnUser.role_ids = user.role_ids;
        returnUser.active = user.active;
        return returnUser;
    };
    return User;
}());
exports.User = User;
