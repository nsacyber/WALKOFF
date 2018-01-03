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
var SettingsService = (function () {
    function SettingsService(authHttp) {
        this.authHttp = authHttp;
    }
    SettingsService.prototype.getConfiguration = function () {
        return this.authHttp.get('/api/configuration')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    SettingsService.prototype.updateConfiguration = function (configuration) {
        return this.authHttp.post('/api/configuration', configuration)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    SettingsService.prototype.getUsers = function () {
        return this.authHttp.get('/api/users')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    SettingsService.prototype.addUser = function (user) {
        return this.authHttp.put('/api/users', user)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    SettingsService.prototype.editUser = function (user) {
        return this.authHttp.post('/api/users', user)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    SettingsService.prototype.deleteUser = function (id) {
        return this.authHttp.delete("/api/users/" + id)
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    SettingsService.prototype.getRoles = function () {
        return this.authHttp.get('/api/roles')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    SettingsService.prototype.addRole = function (role) {
        return this.authHttp.put('/api/roles', role)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    SettingsService.prototype.editRole = function (role) {
        return this.authHttp.post('/api/roles', role)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    SettingsService.prototype.deleteRole = function (id) {
        return this.authHttp.delete("/api/roles/" + id)
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    SettingsService.prototype.getAvailableResourceActions = function () {
        return this.authHttp.get('/api/availableresourceactions')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    SettingsService.prototype.extractData = function (res) {
        var body = res.json();
        return body || {};
    };
    SettingsService.prototype.handleError = function (error) {
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
    return SettingsService;
}());
SettingsService = __decorate([
    core_1.Injectable(),
    __metadata("design:paramtypes", [angular2_jwt_refresh_1.JwtHttp])
], SettingsService);
exports.SettingsService = SettingsService;
