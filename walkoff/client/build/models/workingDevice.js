"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var device_1 = require("./device");
var WorkingDevice = (function () {
    function WorkingDevice() {
        this.fields = {};
    }
    WorkingDevice.toDevice = function (workingDevice) {
        var out = new device_1.Device();
        out.id = workingDevice.id;
        out.name = workingDevice.name;
        out.description = workingDevice.description;
        out.app_name = workingDevice.app_name;
        out.type = workingDevice.type;
        out.fields = [];
        Object.keys(workingDevice.fields).forEach(function (key) {
            out.fields.push({ name: key, value: workingDevice.fields[key] });
        });
        return out;
    };
    return WorkingDevice;
}());
exports.WorkingDevice = WorkingDevice;
