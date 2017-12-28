"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var scheduledTaskTrigger_1 = require("./scheduledTaskTrigger");
var ScheduledTask = (function () {
    function ScheduledTask() {
        this.task_trigger = new scheduledTaskTrigger_1.ScheduledTaskTrigger();
    }
    return ScheduledTask;
}());
exports.ScheduledTask = ScheduledTask;
