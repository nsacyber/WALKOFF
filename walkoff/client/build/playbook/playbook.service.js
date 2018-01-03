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
var PlaybookService = (function () {
    function PlaybookService(authHttp) {
        this.authHttp = authHttp;
    }
    PlaybookService.prototype.getPlaybooks = function () {
        return this.authHttp.get('/api/playbooks')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    PlaybookService.prototype.renamePlaybook = function (oldName, newName) {
        return this.authHttp.post('/api/playbooks', { name: oldName, new_name: newName })
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    PlaybookService.prototype.duplicatePlaybook = function (oldName, newName) {
        return this.authHttp.post("/api/playbooks/" + oldName + "/copy", { playbook: newName })
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    PlaybookService.prototype.deletePlaybook = function (playbookToDelete) {
        return this.authHttp.delete("/api/playbooks/" + playbookToDelete)
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    PlaybookService.prototype.renameWorkflow = function (playbook, oldName, newName) {
        return this.authHttp.post("/api/playbooks/" + playbook + "/workflows", { name: oldName, new_name: newName })
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    PlaybookService.prototype.duplicateWorkflow = function (playbook, oldName, newName) {
        return this.authHttp.post("/api/playbooks/" + playbook + "/workflows/" + oldName + "/copy", { playbook: playbook, workflow: newName })
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    PlaybookService.prototype.deleteWorkflow = function (playbook, workflowToDelete) {
        return this.authHttp.delete("/api/playbooks/" + playbook + "/workflows/" + workflowToDelete)
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    PlaybookService.prototype.newWorkflow = function (playbook, workflow) {
        return this.authHttp.put("/api/playbooks/" + playbook + "/workflows", { name: workflow })
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    PlaybookService.prototype.saveWorkflow = function (playbookName, workflowName, workflow) {
        return this.authHttp.post("/api/playbooks/" + playbookName + "/workflows/" + workflowName + "/save", workflow)
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    PlaybookService.prototype.loadWorkflow = function (playbook, workflow) {
        return this.authHttp.get("/api/playbooks/" + playbook + "/workflows/" + workflow)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    PlaybookService.prototype.executeWorkflow = function (playbook, workflow) {
        return this.authHttp.post("/api/playbooks/" + playbook + "/workflows/" + workflow + "/execute", {})
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    PlaybookService.prototype.getDevices = function () {
        return this.authHttp.get('/api/devices')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    PlaybookService.prototype.getApis = function () {
        return this.authHttp.get('/api/apps/apis')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    PlaybookService.prototype.getUsers = function () {
        return this.authHttp.get('/api/users')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    PlaybookService.prototype.getRoles = function () {
        return this.authHttp.get('/api/roles')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    PlaybookService.prototype.extractData = function (res) {
        var body = res.json();
        return body || {};
    };
    PlaybookService.prototype.handleError = function (error) {
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
    return PlaybookService;
}());
PlaybookService = __decorate([
    core_1.Injectable(),
    __metadata("design:paramtypes", [angular2_jwt_refresh_1.JwtHttp])
], PlaybookService);
exports.PlaybookService = PlaybookService;
