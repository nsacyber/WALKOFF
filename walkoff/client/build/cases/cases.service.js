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
var CasesService = (function () {
    function CasesService(authHttp) {
        this.authHttp = authHttp;
    }
    CasesService.prototype.getCases = function () {
        return this.authHttp.get('/api/cases')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    CasesService.prototype.getEventsForCase = function (name) {
        return this.authHttp.get("/api/cases/" + name + "/events")
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    CasesService.prototype.addCase = function (caseToAdd) {
        return this.authHttp.put('/api/cases', caseToAdd)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    CasesService.prototype.editCase = function (caseToEdit) {
        return this.authHttp.post('/api/cases', caseToEdit)
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    CasesService.prototype.deleteCase = function (id) {
        return this.authHttp.delete("/api/cases/" + id)
            .toPromise()
            .then(function () { return null; })
            .catch(this.handleError);
    };
    CasesService.prototype.getAvailableSubscriptions = function () {
        return this.authHttp.get('/api/availablesubscriptions')
            .toPromise()
            .then(this.extractData)
            .then(function (data) { return data; })
            .catch(this.handleError);
    };
    CasesService.prototype.getPlaybooks = function () {
        return this.authHttp.get('/api/playbooks?full=true')
            .toPromise()
            .then(this.extractData)
            .catch(this.handleError);
    };
    CasesService.prototype.extractData = function (res) {
        var body = res.json();
        return body || {};
    };
    CasesService.prototype.handleError = function (error) {
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
    return CasesService;
}());
CasesService = __decorate([
    core_1.Injectable(),
    __metadata("design:paramtypes", [angular2_jwt_refresh_1.JwtHttp])
], CasesService);
exports.CasesService = CasesService;
