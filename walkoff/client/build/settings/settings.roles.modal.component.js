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
var ng_bootstrap_1 = require("@ng-bootstrap/ng-bootstrap");
var ng2_toasty_1 = require("ng2-toasty");
var settings_service_1 = require("./settings.service");
var role_1 = require("../models/role");
var SettingsRoleModalComponent = (function () {
    function SettingsRoleModalComponent(settingsService, activeModal, toastyService, toastyConfig) {
        this.settingsService = settingsService;
        this.activeModal = activeModal;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.resourceNames = [];
        this.selectPermissionMapping = {};
        this.newResourceTempIdTracker = -1;
        this.toastyConfig.theme = 'bootstrap';
        this.permissionSelectConfig = {
            width: '100%',
            placeholder: 'Select permission(s) for this resource',
            multiple: true,
            allowClear: true,
            closeOnSelect: false,
        };
    }
    SettingsRoleModalComponent.prototype.ngOnInit = function () {
        var _this = this;
        this.availableResourceActions.forEach(function (ara) {
            var typeName = ara.name;
            if (ara.app_name) {
                typeName += " - " + ara.app_name;
            }
            _this.resourceNames.push(typeName);
        });
        this.workingRole.resources.forEach(function (resource) {
            var matchingAvailableResourceAction = _this.availableResourceActions
                .find(function (a) { return a.name === resource.name && a.app_name === resource.app_name; });
            _this.selectPermissionMapping[resource.resource_id] = matchingAvailableResourceAction.actions.map(function (action) {
                return {
                    id: action,
                    text: action,
                };
            });
        });
    };
    SettingsRoleModalComponent.prototype.addResource = function () {
        var _this = this;
        var selectedAvailableResourceAction = this.availableResourceActions.find(function (a) {
            var selectedInfo = _this.selectedAvailableResourceActionName.split(' - ');
            if (selectedInfo.length === 1) {
                return a.name === selectedInfo[0];
            }
            return a.name === selectedInfo[0] && a.app_name === selectedInfo[1];
        });
        var newResource = {
            resource_id: this.newResourceTempIdTracker--,
            role_id: this.workingRole.id,
            name: selectedAvailableResourceAction.name,
            permissions: [],
        };
        if (selectedAvailableResourceAction.app_name) {
            newResource.app_name = selectedAvailableResourceAction.app_name;
        }
        this.selectPermissionMapping[newResource.resource_id] = selectedAvailableResourceAction.actions.map(function (action) {
            return {
                id: action,
                text: action,
            };
        });
        this.workingRole.resources.push(newResource);
    };
    SettingsRoleModalComponent.prototype.removeResource = function (resource) {
        this.workingRole.resources.splice(this.workingRole.resources.indexOf(resource), 1);
        delete this.selectPermissionMapping[resource.resource_id];
    };
    SettingsRoleModalComponent.prototype.permissionSelectChange = function (event, resource) {
        resource.permissions = event.value;
    };
    SettingsRoleModalComponent.prototype.submit = function () {
        var _this = this;
        var validationMessage = this.validate();
        if (validationMessage) {
            this.toastyService.error(validationMessage);
            return;
        }
        var toSubmit = _.cloneDeep(this.workingRole);
        toSubmit.resources.forEach(function (resource) {
            if (resource.resource_id < 0) {
                delete resource.resource_id;
            }
        });
        if (toSubmit.id) {
            this.settingsService
                .editRole(toSubmit)
                .then(function (role) { return _this.activeModal.close({
                role: role,
                isEdit: true,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
        else {
            this.settingsService
                .addRole(toSubmit)
                .then(function (role) { return _this.activeModal.close({
                role: role,
                isEdit: false,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
    };
    SettingsRoleModalComponent.prototype.validate = function () {
        return '';
    };
    return SettingsRoleModalComponent;
}());
__decorate([
    core_1.Input(),
    __metadata("design:type", role_1.Role)
], SettingsRoleModalComponent.prototype, "workingRole", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], SettingsRoleModalComponent.prototype, "title", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], SettingsRoleModalComponent.prototype, "submitText", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], SettingsRoleModalComponent.prototype, "availableResourceActions", void 0);
SettingsRoleModalComponent = __decorate([
    core_1.Component({
        selector: 'settings-role-modal',
        templateUrl: 'client/settings/settings.roles.modal.html',
        styleUrls: [
            'client/settings/settings.css',
        ],
        providers: [settings_service_1.SettingsService],
    }),
    __metadata("design:paramtypes", [settings_service_1.SettingsService, ng_bootstrap_1.NgbActiveModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], SettingsRoleModalComponent);
exports.SettingsRoleModalComponent = SettingsRoleModalComponent;
