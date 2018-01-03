"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var workingDevice_1 = require("./workingDevice");
var Device = (function () {
    function Device() {
        this.fields = [];
    }
    Device.toWorkingDevice = function (device) {
        var out = new workingDevice_1.WorkingDevice();
        out.id = device.id;
        out.name = device.name;
        out.description = device.description;
        out.app_name = device.app_name;
        out.type = device.type;
        out.fields = {};
        device.fields.forEach(function (element) {
            out.fields[element.name] = element.value !== undefined ? element.value : null;
        });
        return out;
    };
    return Device;
}());
exports.Device = Device;
