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
var forms_1 = require("@angular/forms");
var ng_bootstrap_1 = require("@ng-bootstrap/ng-bootstrap");
var ng2_toasty_1 = require("ng2-toasty");
require("rxjs/add/operator/debounceTime");
var settings_service_1 = require("./settings.service");
var settings_roles_modal_component_1 = require("./settings.roles.modal.component");
var role_1 = require("../models/role");
var SettingsRolesComponent = (function () {
    function SettingsRolesComponent(settingsService, modalService, toastyService, toastyConfig) {
        var _this = this;
        this.settingsService = settingsService;
        this.modalService = modalService;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.availableResourceActions = [];
        this.roles = [];
        this.displayRoles = [];
        this.filterQuery = new forms_1.FormControl();
        this.toastyConfig.theme = 'bootstrap';
        this.getAvailableResourceActions();
        this.getRoles();
        this.filterQuery
            .valueChanges
            .debounceTime(500)
            .subscribe(function (event) { return _this.filterRoles(); });
    }
    SettingsRolesComponent.prototype.filterRoles = function () {
        var searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';
        this.displayRoles = this.roles.filter(function (user) {
            return user.name.toLocaleLowerCase().includes(searchFilter);
        });
    };
    SettingsRolesComponent.prototype.getAvailableResourceActions = function () {
        var _this = this;
        this.settingsService
            .getAvailableResourceActions()
            .then(function (availableResourceActions) { return _this.availableResourceActions = availableResourceActions; })
            .catch(function (e) { return _this.toastyService.error(e.message); });
    };
    SettingsRolesComponent.prototype.getRoles = function () {
        var _this = this;
        this.settingsService
            .getRoles()
            .then(function (roles) { return _this.displayRoles = _this.roles = roles; })
            .catch(function (e) { return _this.toastyService.error(e.message); });
    };
    SettingsRolesComponent.prototype.addRole = function () {
        var modalRef = this.modalService.open(settings_roles_modal_component_1.SettingsRoleModalComponent);
        modalRef.componentInstance.title = 'Add New Role';
        modalRef.componentInstance.submitText = 'Add Role';
        modalRef.componentInstance.availableResourceActions = this.availableResourceActions;
        modalRef.componentInstance.workingRole = new role_1.Role();
        this._handleModalClose(modalRef);
    };
    SettingsRolesComponent.prototype.editRole = function (role) {
        var modalRef = this.modalService.open(settings_roles_modal_component_1.SettingsRoleModalComponent);
        modalRef.componentInstance.title = "Edit Role: " + role.name;
        modalRef.componentInstance.submitText = 'Save Changes';
        modalRef.componentInstance.availableResourceActions = this.availableResourceActions;
        modalRef.componentInstance.workingRole = _.cloneDeep(role);
        this._handleModalClose(modalRef);
    };
    SettingsRolesComponent.prototype.deleteRole = function (roleToDelete) {
        var _this = this;
        if (!confirm("Are you sure you want to delete the role \"" + roleToDelete.name + "\"?")) {
            return;
        }
        this.settingsService
            .deleteRole(roleToDelete.id)
            .then(function () {
            _this.roles = _this.roles.filter(function (role) { return role.id !== roleToDelete.id; });
            _this.filterRoles();
            _this.toastyService.success("Role \"" + roleToDelete.name + "\" successfully deleted.");
        })
            .catch(function (e) { return _this.toastyService.error(e.message); });
    };
    SettingsRolesComponent.prototype.getFriendlyPermissions = function (role) {
        var obj = role.resources.reduce(function (accumulator, resource) {
            var key = resource.name;
            if (resource.app_name) {
                key += " - " + resource.app_name;
            }
            accumulator[key] = resource.permissions;
            return accumulator;
        }, {});
        var out = JSON.stringify(obj, null, 1);
        out = out.replace(/[\{\}"]/g, '').trim();
        return out;
    };
    SettingsRolesComponent.prototype._handleModalClose = function (modalRef) {
        var _this = this;
        modalRef.result
            .then(function (result) {
            if (!result || !result.role) {
                return;
            }
            if (result.isEdit) {
                var toUpdate = _this.roles.find(function (r) { return r.id === result.role.id; });
                Object.assign(toUpdate, result.role);
                _this.filterRoles();
                _this.toastyService.success("Role \"" + result.role.name + "\" successfully edited.");
            }
            else {
                _this.roles.push(result.role);
                _this.filterRoles();
                _this.toastyService.success("Role \"" + result.role.name + "\" successfully added.");
            }
        }, function (error) { if (error) {
            _this.toastyService.error(error.message);
        } });
    };
    return SettingsRolesComponent;
}());
SettingsRolesComponent = __decorate([
    core_1.Component({
        selector: 'settings-roles-component',
        templateUrl: 'client/settings/settings.roles.html',
        styleUrls: [
            'client/settings/settings.css',
        ],
        encapsulation: core_1.ViewEncapsulation.None,
        providers: [settings_service_1.SettingsService],
    }),
    __metadata("design:paramtypes", [settings_service_1.SettingsService, ng_bootstrap_1.NgbModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], SettingsRolesComponent);
exports.SettingsRolesComponent = SettingsRolesComponent;
