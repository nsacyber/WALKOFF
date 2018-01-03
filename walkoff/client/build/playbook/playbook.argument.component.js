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
var parameterApi_1 = require("../models/api/parameterApi");
var argument_1 = require("../models/playbook/argument");
var AVAILABLE_TYPES = ['string', 'number', 'boolean'];
var PlaybookArgumentComponent = (function () {
    function PlaybookArgumentComponent() {
        this.propertyName = '';
        this.availableTypes = AVAILABLE_TYPES;
        this.arrayTypes = [];
        this.objectTypes = {};
    }
    PlaybookArgumentComponent.prototype.ngOnInit = function () {
        this.parameterSchema = this.parameterApi.schema;
        if (this.argument.reference == null) {
            this.argument.reference = '';
        }
        if (this.argument.value == null) {
            if (this.parameterSchema.type === 'array') {
                this.argument.value = [];
            }
            else if (this.parameterSchema.type === 'object') {
                this.argument.value = {};
            }
        }
        else if (this.parameterSchema.type === 'array') {
            for (var _i = 0, _a = this.argument.value; _i < _a.length; _i++) {
                var item = _a[_i];
                this.arrayTypes.push(typeof (item));
            }
        }
        else if (this.parameterSchema.type === 'object') {
            for (var key in this.argument.value) {
                if (this.argument.value.hasOwnProperty(key)) {
                    this.objectTypes[key] = typeof (this.argument.value[key]);
                }
            }
        }
        this.selectedType = this.availableTypes[0];
        if (this.isUserSelect(this.parameterSchema)) {
            this.selectData = this.users.map(function (user) {
                return { id: user.id.toString(), text: user.username };
            });
            this.selectConfig = {
                width: '100%',
                placeholder: 'Select user',
            };
            if (this.parameterSchema.type === 'array') {
                this.selectConfig.placeholder += '(s)';
                this.selectConfig.multiple = true;
                this.selectConfig.allowClear = true;
                this.selectConfig.closeOnSelect = false;
            }
            this.selectInitialValue = JSON.parse(JSON.stringify(this.argument.value));
        }
        if (this.isRoleSelect(this.parameterSchema)) {
            this.selectData = this.roles.map(function (role) {
                return { id: role.id.toString(), text: role.name };
            });
            this.selectConfig = {
                width: '100%',
                placeholder: 'Select role',
            };
            if (this.parameterSchema.type === 'array') {
                this.selectConfig.placeholder += '(s)';
                this.selectConfig.multiple = true;
                this.selectConfig.allowClear = true;
                this.selectConfig.closeOnSelect = false;
            }
            this.selectInitialValue = JSON.parse(JSON.stringify(this.argument.value));
        }
    };
    PlaybookArgumentComponent.prototype.selectChange = function ($event) {
        if (this.parameterSchema.type === 'array') {
            var array = $event.value.map(function (id) { return +id; });
            this.argument.value = array;
        }
        else {
            this.argument.value = +$event.value;
        }
    };
    PlaybookArgumentComponent.prototype.addItem = function () {
        switch (this.selectedType) {
            case 'string':
                this.argument.value.push('');
                break;
            case 'number':
                this.argument.value.push(null);
                break;
            case 'boolean':
                this.argument.value.push(false);
                break;
            default:
                return;
        }
        this.arrayTypes.push(this.selectedType);
    };
    PlaybookArgumentComponent.prototype.moveUp = function (index) {
        var idAbove = index - 1;
        var toBeSwapped = this.argument.value[idAbove];
        var arrayTypeToBeSwapped = this.arrayTypes[idAbove];
        this.argument.value[idAbove] = this.argument.value[index];
        this.argument.value[index] = toBeSwapped;
        this.arrayTypes[idAbove] = this.arrayTypes[index];
        this.arrayTypes[index] = arrayTypeToBeSwapped;
    };
    PlaybookArgumentComponent.prototype.moveDown = function (index) {
        var idBelow = index + 1;
        var toBeSwapped = this.argument.value[idBelow];
        var arrayTypeToBeSwapped = this.arrayTypes[idBelow];
        this.argument.value[idBelow] = this.argument.value[index];
        this.argument.value[index] = toBeSwapped;
        this.arrayTypes[idBelow] = this.arrayTypes[index];
        this.arrayTypes[index] = arrayTypeToBeSwapped;
    };
    PlaybookArgumentComponent.prototype.removeItem = function (index) {
        this.argument.value.splice(index, 1);
        this.arrayTypes.splice(index, 1);
    };
    PlaybookArgumentComponent.prototype.addProperty = function () {
        if (this.argument.value.hasOwnProperty(this.propertyName)) {
            return;
        }
        this.propertyName = this.propertyName.trim();
        switch (this.selectedType) {
            case 'string':
                this.argument.value[this.propertyName] = '';
                break;
            case 'number':
                this.argument.value[this.propertyName] = null;
                break;
            case 'boolean':
                this.argument.value[this.propertyName] = false;
                break;
            default:
                return;
        }
        this.objectTypes[this.propertyName] = this.selectedType;
        this.propertyName = '';
    };
    PlaybookArgumentComponent.prototype.removeProperty = function (key) {
        delete this.argument.value[key];
        delete this.objectTypes[key];
    };
    PlaybookArgumentComponent.prototype.trackArraysBy = function (index, item) {
        return index;
    };
    PlaybookArgumentComponent.prototype.getPreviousActions = function () {
        return this.loadedWorkflow.actions;
    };
    PlaybookArgumentComponent.prototype.getMin = function (schema) {
        if (schema.minimum === undefined) {
            return null;
        }
        if (schema.exclusiveMinimum) {
            return schema.minimum + 1;
        }
        return schema.minimum;
    };
    PlaybookArgumentComponent.prototype.getMax = function (schema) {
        if (schema.maximum === undefined) {
            return null;
        }
        if (schema.exclusiveMaximum) {
            return schema.maximum - 1;
        }
        return schema.maximum;
    };
    PlaybookArgumentComponent.prototype.isNormalArray = function (schema) {
        if (schema.type !== 'array') {
            return false;
        }
        if (Array.isArray(schema.items)) {
            schema.items.forEach(function (i) {
                if (i.type === 'user' || i.type === 'role') {
                    return false;
                }
            });
        }
        else if (schema.items.type === 'user' || schema.items.type === 'role') {
            return false;
        }
        return true;
    };
    PlaybookArgumentComponent.prototype.isUserSelect = function (schema) {
        if (schema.type === 'user' ||
            (schema.type === 'array' && schema.items && !Array.isArray(schema.items) && schema.items.type === 'user')) {
            return true;
        }
        return false;
    };
    PlaybookArgumentComponent.prototype.isRoleSelect = function (schema) {
        if (schema.type === 'role' ||
            (schema.type === 'array' && schema.items && !Array.isArray(schema.items) && schema.items.type === 'role')) {
            return true;
        }
        return false;
    };
    return PlaybookArgumentComponent;
}());
__decorate([
    core_1.Input(),
    __metadata("design:type", Number)
], PlaybookArgumentComponent.prototype, "id", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", argument_1.Argument)
], PlaybookArgumentComponent.prototype, "argument", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", parameterApi_1.ParameterApi)
], PlaybookArgumentComponent.prototype, "parameterApi", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", workflow_1.Workflow)
], PlaybookArgumentComponent.prototype, "loadedWorkflow", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], PlaybookArgumentComponent.prototype, "users", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], PlaybookArgumentComponent.prototype, "roles", void 0);
PlaybookArgumentComponent = __decorate([
    core_1.Component({
        selector: 'playbook-argument-component',
        templateUrl: 'client/playbook/playbook.argument.html',
        styleUrls: [],
        encapsulation: core_1.ViewEncapsulation.None,
        providers: [playbook_service_1.PlaybookService],
    }),
    __metadata("design:paramtypes", [])
], PlaybookArgumentComponent);
exports.PlaybookArgumentComponent = PlaybookArgumentComponent;
