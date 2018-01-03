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
var angular2_jwt_1 = require("angular2-jwt");
var angular2_jwt_refresh_1 = require("angular2-jwt-refresh");
var REFRESH_TOKEN_NAME = 'refresh_token';
var ACCESS_TOKEN_NAME = 'access_token';
var AuthService = (function () {
    function AuthService(authHttp, http) {
        this.authHttp = authHttp;
        this.http = http;
        this.jwtHelper = new angular2_jwt_1.JwtHelper();
    }
    AuthService.prototype.login = function (username, password) {
        return this.authHttp.post('/api/auth', { username: username, password: password })
            .toPromise()
            .then(this.extractData)
            .then(function (tokens) {
            sessionStorage.setItem(ACCESS_TOKEN_NAME, tokens.access_token);
            sessionStorage.setItem(REFRESH_TOKEN_NAME, tokens.refresh_token);
            location.href = '/';
        })
            .catch(this.handleError);
    };
    AuthService.prototype.logout = function () {
        var _this = this;
        return this.authHttp.post('/api/auth/logout', { refresh_token: sessionStorage.getItem(REFRESH_TOKEN_NAME) })
            .toPromise()
            .then(function () {
            _this.clearTokens();
            location.href = '/login';
        })
            .catch(this.handleError);
    };
    AuthService.prototype.clearTokens = function () {
        sessionStorage.removeItem(ACCESS_TOKEN_NAME);
        sessionStorage.removeItem(REFRESH_TOKEN_NAME);
    };
    AuthService.prototype.canAccess = function (resourceName, actionName) {
        return false;
    };
    AuthService.prototype.getRefreshToken = function () {
        return sessionStorage.getItem(REFRESH_TOKEN_NAME);
    };
    AuthService.prototype.getAccessToken = function () {
        return sessionStorage.getItem(ACCESS_TOKEN_NAME);
    };
    AuthService.prototype.getAccessTokenRefreshed = function () {
        var token = this.getAccessToken();
        if (!this.jwtHelper.isTokenExpired(token)) {
            return Promise.resolve(token);
        }
        var refreshToken = this.getRefreshToken();
        if (!refreshToken || this.jwtHelper.isTokenExpired(refreshToken)) {
            return Promise.reject('Refresh token does not exist or has expired. Please log in again.');
        }
        var headers = new http_1.Headers({ Authorization: "Bearer " + this.getRefreshToken() });
        return this.http.post('/api/auth/refresh', {}, { headers: headers })
            .toPromise()
            .then(this.extractData)
            .then(function (refreshedToken) { return refreshedToken.access_token; })
            .catch(this.handleError);
    };
    AuthService.prototype.getAndDecodeRefreshToken = function () {
        return this.jwtHelper.decodeToken(this.getRefreshToken());
    };
    AuthService.prototype.getAndDecodeAccessToken = function () {
        return this.jwtHelper.decodeToken(this.getAccessToken());
    };
    AuthService.prototype.isAccessTokenFresh = function () {
        return !!this.getAndDecodeAccessToken().fresh;
    };
    AuthService.prototype.extractData = function (res) {
        var body = res.json();
        return body || {};
    };
    AuthService.prototype.handleError = function (error) {
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
    return AuthService;
}());
AuthService = __decorate([
    core_1.Injectable(),
    __metadata("design:paramtypes", [angular2_jwt_refresh_1.JwtHttp, http_1.Http])
], AuthService);
exports.AuthService = AuthService;
