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
var playbook_service_1 = require("./playbook.service");
var workflow_1 = require("../models/playbook/workflow");
var transform_1 = require("../models/playbook/transform");
var PlaybookTransformsComponent = (function () {
    function PlaybookTransformsComponent() {
    }
    PlaybookTransformsComponent.prototype.ngOnInit = function () {
        var _this = this;
        var appsWithTransforms = this.appApis.filter(function (app) { return app.transform_apis && app.transform_apis.length; });
        if (!appsWithTransforms.find(function (a) { return a.name === _this.selectedAppName; })) {
            var firstApp = appsWithTransforms[0];
            if (firstApp) {
                this.selectedAppName = firstApp.name;
            }
        }
        this.appNamesWithTransforms = appsWithTransforms.map(function (app) { return app.name; });
        this.resetTransformSelection(this.selectedAppName);
    };
    PlaybookTransformsComponent.prototype.resetTransformSelection = function (appName) {
        var app = this.appApis.find(function (a) { return a.name === appName; });
        if (app.transform_apis && app.transform_apis.length) {
            this.selectedTransformApi = app.transform_apis[0].name;
        }
    };
    PlaybookTransformsComponent.prototype.addTransform = function () {
        if (!this.selectedAppName || !this.selectedTransformApi) {
            return;
        }
        var newTransform = new transform_1.Transform();
        newTransform.app_name = this.selectedAppName;
        newTransform.action_name = this.selectedTransformApi;
        this.transforms.push(newTransform);
    };
    PlaybookTransformsComponent.prototype.moveUp = function (index) {
        var idAbove = index - 1;
        var toBeSwapped = this.transforms[idAbove];
        this.transforms[idAbove] = this.transforms[index];
        this.transforms[index] = toBeSwapped;
    };
    PlaybookTransformsComponent.prototype.moveDown = function (index) {
        var idBelow = index + 1;
        var toBeSwapped = this.transforms[idBelow];
        this.transforms[idBelow] = this.transforms[index];
        this.transforms[index] = toBeSwapped;
    };
    PlaybookTransformsComponent.prototype.removeTransform = function (index) {
        this.transforms.splice(index, 1);
    };
    PlaybookTransformsComponent.prototype.getTransformApi = function (appName, transformName) {
        var transformApi = this.appApis.find(function (a) { return a.name === appName; }).transform_apis.find(function (t) { return t.name === transformName; });
        transformApi.parameters = transformApi.parameters.filter(function (p) { return p.name !== transformApi.data_in; });
        return transformApi;
    };
    PlaybookTransformsComponent.prototype.getOrInitializeArgument = function (transform, parameterApi) {
        var argument = transform.arguments.find(function (a) { return a.name === parameterApi.name; });
        if (argument) {
            return argument;
        }
        argument = this.getDefaultArgument(parameterApi);
        transform.arguments.push(argument);
        return argument;
    };
    PlaybookTransformsComponent.prototype.getDefaultArgument = function (parameterApi) {
        return {
            name: parameterApi.name,
            value: parameterApi.schema.default != null ? parameterApi.schema.default : null,
            reference: '',
            selection: '',
        };
    };
    PlaybookTransformsComponent.prototype.getTransformNamesForApp = function () {
        var _this = this;
        return this.appApis.find(function (a) { return a.name === _this.selectedAppName; }).transform_apis.map(function (c) { return c.name; });
    };
    return PlaybookTransformsComponent;
}());
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], PlaybookTransformsComponent.prototype, "selectedAppName", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], PlaybookTransformsComponent.prototype, "transforms", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], PlaybookTransformsComponent.prototype, "appApis", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", workflow_1.Workflow)
], PlaybookTransformsComponent.prototype, "loadedWorkflow", void 0);
PlaybookTransformsComponent = __decorate([
    core_1.Component({
        selector: 'playbook-transforms-component',
        templateUrl: 'client/playbook/playbook.transforms.html',
        styleUrls: [],
        encapsulation: core_1.ViewEncapsulation.None,
        providers: [playbook_service_1.PlaybookService],
    }),
    __metadata("design:paramtypes", [])
], PlaybookTransformsComponent);
exports.PlaybookTransformsComponent = PlaybookTransformsComponent;
