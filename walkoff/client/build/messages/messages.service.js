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
var argument_1 = require("../models/playbook/argument");
var MessagesService = (function () {
    function MessagesService(authHttp) {
        this.authHttp = authHttp;
    }
    MessagesService.prototype.listMessages = function () {
        return this.authHttp.get('/api/messages')
            .toPromise()
            .then(this.extractData)
            .then(function (messageListing) { return messageListing; })
            .catch(this.handleError);
    };
    MessagesService.prototype.getMessage = function (messageId) {
        return this.authHttp.get("/api/messages/" + messageId)
            .toPromise()
            .then(this.extractData)
            .then(function (message) { return message; })
            .catch(this.handleError);
    };
    MessagesService.prototype.deleteMessages = function (messageIds) {
        if (!Array.isArray(messageIds)) {
            messageIds = [messageIds];
        }
        return this.authHttp.post('/api/messages/delete', { ids: messageIds })
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    MessagesService.prototype.readMessages = function (messageIds) {
        if (!Array.isArray(messageIds)) {
            messageIds = [messageIds];
        }
        return this.authHttp.post('/api/messages/read', { ids: messageIds })
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    MessagesService.prototype.unreadMessages = function (messageIds) {
        if (!Array.isArray(messageIds)) {
            messageIds = [messageIds];
        }
        return this.authHttp.post('/api/messages/unread', { ids: messageIds })
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    MessagesService.prototype.performMessageAction = function (execution_uid, action) {
        var arg = new argument_1.Argument();
        arg.name = 'action';
        arg.value = action;
        var body = {
            execution_uids: [execution_uid],
            data_in: action,
            arguments: [arg],
        };
        return this.authHttp.post('/api/triggers/send_data', body)
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    MessagesService.prototype.extractData = function (res) {
        var body = res.json();
        return body || {};
    };
    MessagesService.prototype.handleError = function (error) {
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
    return MessagesService;
}());
MessagesService = __decorate([
    core_1.Injectable(),
    __metadata("design:paramtypes", [angular2_jwt_refresh_1.JwtHttp])
], MessagesService);
exports.MessagesService = MessagesService;
