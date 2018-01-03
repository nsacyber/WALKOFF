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
var MainService = (function () {
    function MainService(authHttp) {
        this.authHttp = authHttp;
    }
    MainService.prototype.getInterfaceNamess = function () {
        return this.authHttp.get('/api/interfaces')
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    MainService.prototype.getInitialNotifications = function () {
        return this.authHttp.get('/api/notifications')
            .toPromise()
            .then(this.extractData)
            .then(function (messageListing) { return messageListing; })
            .catch(this.handleError);
    };
    MainService.prototype.getMessage = function (messageId) {
        return this.authHttp.get("/api/messages/" + messageId)
            .toPromise()
            .then(this.extractData)
            .then(function (message) { return message; })
            .catch(this.handleError);
    };
    MainService.prototype.extractData = function (res) {
        var body = res.json();
        return body || {};
    };
    MainService.prototype.handleError = function (error) {
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
    return MainService;
}());
MainService = __decorate([
    core_1.Injectable(),
    __metadata("design:paramtypes", [angular2_jwt_refresh_1.JwtHttp])
], MainService);
exports.MainService = MainService;
