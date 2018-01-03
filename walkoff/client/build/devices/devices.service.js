"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
Object.defineProperty(exports, "__esModule", { value: true });
var core_1 = require("@angular/core");
var http_1 = require("@angular/http");
var angular2_jwt_refresh_1 = require("angular2-jwt-refresh");
var DevicesService = (function () {
    function DevicesService(authHttp) {
        this.authHttp = authHttp;
    }
    DevicesService.prototype.getDevicesForApp = function (appName) {
        return this.authHttp.get("/api/apps/" + appName)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    DevicesService.prototype.getAppDevice = function (appName, deviceName) {
        return this.authHttp.get("/api/apps/" + appName + "/devices/" + deviceName)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    DevicesService.prototype.getDevices = function () {
        return this.authHttp.get('/api/devices')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    DevicesService.prototype.addDevice = function (device) {
        return this.authHttp.put('/api/devices', device)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    DevicesService.prototype.editDevice = function (device) {
        return this.authHttp.post('/api/devices', device)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    DevicesService.prototype.deleteDevice = function (deviceId) {
        return this.authHttp.delete("/api/devices/" + deviceId)
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    DevicesService.prototype.getDeviceApis = function () {
        return this.authHttp.get('api/apps/apis?field_name=device_apis')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .then(function (appApis) { return appApis.filter(function (a) { return a.device_apis && a.device_apis.length; }); })
            .catch(this.handleError);
    };
    DevicesService.prototype.extractData = function (res) {
        var body = res.json();
        return body || {};
    };
    DevicesService.prototype.handleError = function (error) {
        var errMsg;
        var err;
        if (error instanceof http_1.Response) {
            var body = error.json() || '';
            err = body.error || body.detail || JSON.stringify(body);
            errMsg = error.status + " - " + (error.statusText || '') + " " + err;
        }
        else {
            err = errMsg = error.message ? error.message : error.toString();
        }
        console.error(errMsg);
        throw new Error(err);
    };
    return DevicesService;
}());
DevicesService = __decorate([
    core_1.Injectable(),
    __metadata("design:paramtypes", [angular2_jwt_refresh_1.JwtHttp])
], DevicesService);
exports.DevicesService = DevicesService;
