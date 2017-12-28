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
var condition_1 = require("../models/playbook/condition");
var PlaybookConditionsComponent = (function () {
    function PlaybookConditionsComponent() {
    }
    PlaybookConditionsComponent.prototype.ngOnInit = function () {
        var _this = this;
        var appsWithConditions = this.appApis.filter(function (app) { return app.condition_apis && app.condition_apis.length; });
        if (!appsWithConditions.find(function (a) { return a.name === _this.selectedAppName; })) {
            var firstApp = appsWithConditions[0];
            if (firstApp) {
                this.selectedAppName = firstApp.name;
            }
        }
        this.appNamesWithConditions = appsWithConditions.map(function (app) { return app.name; });
        this.resetConditionSelection(this.selectedAppName);
    };
    PlaybookConditionsComponent.prototype.resetConditionSelection = function (appName) {
        var app = this.appApis.find(function (a) { return a.name === appName; });
        if (app.condition_apis && app.condition_apis.length) {
            this.selectedConditionApi = app.condition_apis[0].name;
        }
    };
    PlaybookConditionsComponent.prototype.addCondition = function () {
        if (!this.selectedAppName || !this.selectedConditionApi) {
            return;
        }
        var newCondition = new condition_1.Condition();
        newCondition.app_name = this.selectedAppName;
        newCondition.action_name = this.selectedConditionApi;
        this.conditions.push(newCondition);
    };
    PlaybookConditionsComponent.prototype.moveUp = function (index) {
        var idAbove = index - 1;
        var toBeSwapped = this.conditions[idAbove];
        this.conditions[idAbove] = this.conditions[index];
        this.conditions[index] = toBeSwapped;
    };
    PlaybookConditionsComponent.prototype.moveDown = function (index) {
        var idBelow = index + 1;
        var toBeSwapped = this.conditions[idBelow];
        this.conditions[idBelow] = this.conditions[index];
        this.conditions[index] = toBeSwapped;
    };
    PlaybookConditionsComponent.prototype.removeCondition = function (index) {
        this.conditions.splice(index, 1);
    };
    PlaybookConditionsComponent.prototype.getConditionApi = function (appName, conditionName) {
        var conditionApi = this.appApis.find(function (a) { return a.name === appName; }).condition_apis.find(function (c) { return c.name === conditionName; });
        conditionApi.parameters = conditionApi.parameters.filter(function (p) { return p.name !== conditionApi.data_in; });
        return conditionApi;
    };
    PlaybookConditionsComponent.prototype.getOrInitializeArgument = function (condition, parameterApi) {
        var argument = condition.arguments.find(function (a) { return a.name === parameterApi.name; });
        if (argument) {
            return argument;
        }
        argument = this.getDefaultArgument(parameterApi);
        condition.arguments.push(argument);
        return argument;
    };
    PlaybookConditionsComponent.prototype.getDefaultArgument = function (parameterApi) {
        return {
            name: parameterApi.name,
            value: parameterApi.schema.default != null ? parameterApi.schema.default : null,
            reference: '',
            selection: '',
        };
    };
    PlaybookConditionsComponent.prototype.getConditionNamesForApp = function () {
        var _this = this;
        return this.appApis.find(function (a) { return a.name === _this.selectedAppName; }).condition_apis.map(function (c) { return c.name; });
    };
    return PlaybookConditionsComponent;
}());
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], PlaybookConditionsComponent.prototype, "selectedAppName", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], PlaybookConditionsComponent.prototype, "conditions", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], PlaybookConditionsComponent.prototype, "appApis", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", workflow_1.Workflow)
], PlaybookConditionsComponent.prototype, "loadedWorkflow", void 0);
PlaybookConditionsComponent = __decorate([
    core_1.Component({
        selector: 'playbook-conditions-component',
        templateUrl: 'client/playbook/playbook.conditions.html',
        styleUrls: [],
        encapsulation: core_1.ViewEncapsulation.None,
        providers: [playbook_service_1.PlaybookService],
    }),
    __metadata("design:paramtypes", [])
], PlaybookConditionsComponent);
exports.PlaybookConditionsComponent = PlaybookConditionsComponent;
