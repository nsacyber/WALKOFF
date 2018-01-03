"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var angular2_uuid_1 = require("angular2-uuid");
var Workflow = (function () {
    function Workflow() {
        this.uid = angular2_uuid_1.UUID.UUID();
        this.actions = [];
        this.branches = [];
    }
    return Workflow;
}());
exports.Workflow = Workflow;
