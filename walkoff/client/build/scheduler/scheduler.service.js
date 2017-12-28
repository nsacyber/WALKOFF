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
require("rxjs/add/operator/map");
require("rxjs/add/operator/toPromise");
var schedulerStatusNumberMapping = {
    0: 'stopped',
    1: 'running',
    2: 'paused',
};
var SchedulerService = (function () {
    function SchedulerService(authHttp) {
        this.authHttp = authHttp;
    }
    SchedulerService.prototype.executeWorkflow = function (playbook, workflow) {
        return this.authHttp.post("/playbooks/" + playbook + "/workflows/" + workflow + "/execute", {})
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    SchedulerService.prototype.getSchedulerStatus = function () {
        return this.authHttp.get('/api/scheduler')
            .toPromise()
            .then(this.extractData)
            .then(function (statusObj) { return schedulerStatusNumberMapping[statusObj.status]; })
            .catch(this.handleError);
    };
    SchedulerService.prototype.changeSchedulerStatus = function (status) {
        return this.authHttp.get("/api/scheduler/" + status)
            .toPromise()
            .then(this.extractData)
            .then(function (statusObj) { return schedulerStatusNumberMapping[statusObj.status]; })
            .catch(this.handleError);
    };
    SchedulerService.prototype.getScheduledTasks = function () {
        return this.authHttp.get('/api/scheduledtasks')
            .toPromise()
            .then(this.extractData)
            .then(function (scheduledTasks) { return scheduledTasks; })
            .catch(this.handleError);
    };
    SchedulerService.prototype.addScheduledTask = function (scheduledTask) {
        return this.authHttp.put('/api/scheduledtasks', scheduledTask)
            .toPromise()
            .then(this.extractData)
            .then(function (newScheduledTask) { return newScheduledTask; })
            .catch(this.handleError);
    };
    SchedulerService.prototype.editScheduledTask = function (scheduledTask) {
        return this.authHttp.post('/api/scheduledtasks', scheduledTask)
            .toPromise()
            .then(this.extractData)
            .then(function (editedScheduledTask) { return editedScheduledTask; })
            .catch(this.handleError);
    };
    SchedulerService.prototype.deleteScheduledTask = function (scheduledTaskId) {
        return this.authHttp.delete("/api/scheduledtasks/" + scheduledTaskId)
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    SchedulerService.prototype.changeScheduledTaskStatus = function (scheduledTaskId, actionName) {
        return this.authHttp.put("/api/scheduledtasks/" + scheduledTaskId + "/" + actionName, {})
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    SchedulerService.prototype.getPlaybooks = function () {
        return this.authHttp.get('/api/playbooks')
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    SchedulerService.prototype.extractData = function (res) {
        var body = res.json();
        return body || {};
    };
    SchedulerService.prototype.handleError = function (error) {
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
    return SchedulerService;
}());
SchedulerService = __decorate([
    core_1.Injectable(),
    __metadata("design:paramtypes", [angular2_jwt_refresh_1.JwtHttp])
], SchedulerService);
exports.SchedulerService = SchedulerService;
