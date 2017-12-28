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
var _ = require("lodash");
var ng_bootstrap_1 = require("@ng-bootstrap/ng-bootstrap");
var ng2_toasty_1 = require("ng2-toasty");
require("rxjs/add/operator/debounceTime");
var settings_service_1 = require("./settings.service");
var settings_user_modal_component_1 = require("./settings.user.modal.component");
var configuration_1 = require("../models/configuration");
var user_1 = require("../models/user");
var workingUser_1 = require("../models/workingUser");
var SettingsComponent = (function () {
    function SettingsComponent(settingsService, modalService, toastyService, toastyConfig) {
        var _this = this;
        this.settingsService = settingsService;
        this.modalService = modalService;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.configuration = new configuration_1.Configuration();
        this.dbTypes = ['sqlite', 'mysql', 'postgresql', 'oracle', 'mssql'];
        this.tlsVersions = ['1.1', '1.2', '1.3'];
        this.users = [];
        this.displayUsers = [];
        this.filterQuery = new forms_1.FormControl();
        this.roles = [];
        this.toastyConfig.theme = 'bootstrap';
        this.getConfiguration();
        this.getUsers();
        this.getRoles();
        this.filterQuery
            .valueChanges
            .debounceTime(500)
            .subscribe(function (event) { return _this.filterUsers(); });
    }
    SettingsComponent.prototype.filterUsers = function () {
        var searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';
        this.displayUsers = this.users.filter(function (user) {
            return user.username.toLocaleLowerCase().includes(searchFilter);
        });
    };
    SettingsComponent.prototype.getConfiguration = function () {
        var _this = this;
        this.settingsService
            .getConfiguration()
            .then(function (configuration) { return Object.assign(_this.configuration, configuration); })
            .catch(function (e) { return _this.toastyService.error(e.message); });
    };
    SettingsComponent.prototype.updateConfiguration = function () {
        var _this = this;
        this.settingsService
            .updateConfiguration(this.configuration)
            .then(function (configuration) {
            Object.assign(_this.configuration, configuration);
            _this.toastyService.success('Configuration successfully updated.');
        })
            .catch(function (e) { return _this.toastyService.error(e.message); });
    };
    SettingsComponent.prototype.resetConfiguration = function () {
        if (!confirm("Are you sure you want to reset the configuration? \
			Note that you'll have to save the configuration after reset to update it on the server.")) {
            return;
        }
        Object.assign(this.configuration, configuration_1.Configuration.getDefaultConfiguration());
    };
    SettingsComponent.prototype.getRoles = function () {
        var _this = this;
        this.settingsService
            .getRoles()
            .then(function (roles) { return _this.roles = roles; })
            .catch(function (e) { return _this.toastyService.error("Error retrieving roles: " + e.message); });
    };
    SettingsComponent.prototype.getUsers = function () {
        var _this = this;
        this.settingsService
            .getUsers()
            .then(function (users) { return _this.displayUsers = _this.users = users; })
            .catch(function (e) { return _this.toastyService.error("Error retrieving users: " + e.message); });
    };
    SettingsComponent.prototype.addUser = function () {
        var modalRef = this.modalService.open(settings_user_modal_component_1.SettingsUserModalComponent);
        modalRef.componentInstance.title = 'Add New User';
        modalRef.componentInstance.submitText = 'Add User';
        modalRef.componentInstance.roles = this.roles;
        var workingUser = new workingUser_1.WorkingUser();
        workingUser.active = true;
        modalRef.componentInstance.workingUser = workingUser;
        this._handleModalClose(modalRef);
    };
    SettingsComponent.prototype.editUser = function (user) {
        var modalRef = this.modalService.open(settings_user_modal_component_1.SettingsUserModalComponent);
        modalRef.componentInstance.title = "Edit User: " + user.username;
        modalRef.componentInstance.submitText = 'Save Changes';
        modalRef.componentInstance.roles = this.roles;
        modalRef.componentInstance.workingUser = user_1.User.toWorkingUser(user);
        this._handleModalClose(modalRef);
    };
    SettingsComponent.prototype.deleteUser = function (userToDelete) {
        var _this = this;
        if (!confirm("Are you sure you want to delete the user \"" + userToDelete.username + "\"?")) {
            return;
        }
        this.settingsService
            .deleteUser(userToDelete.id)
            .then(function () {
            _this.users = _.reject(_this.users, function (user) { return user.id === userToDelete.id; });
            _this.filterUsers();
            _this.toastyService.success("User \"" + userToDelete.username + "\" successfully deleted.");
        })
            .catch(function (e) { return _this.toastyService.error(e.message); });
    };
    SettingsComponent.prototype.getFriendlyRoles = function (roles) {
        return _.map(roles, 'name').join(', ');
    };
    SettingsComponent.prototype.getFriendlyBool = function (val) {
        return val ? 'Yes' : 'No';
    };
    SettingsComponent.prototype._handleModalClose = function (modalRef) {
        var _this = this;
        modalRef.result
            .then(function (result) {
            if (!result || !result.user) {
                return;
            }
            if (result.isEdit) {
                var toUpdate = _.find(_this.users, function (u) { return u.id === result.user.id; });
                Object.assign(toUpdate, result.user);
                _this.filterUsers();
                _this.toastyService.success("User \"" + result.user.username + "\" successfully edited.");
            }
            else {
                _this.users.push(result.user);
                _this.filterUsers();
                _this.toastyService.success("User \"" + result.user.username + "\" successfully added.");
            }
        }, function (error) { if (error) {
            _this.toastyService.error(error.message);
        } });
    };
    return SettingsComponent;
}());
SettingsComponent = __decorate([
    core_1.Component({
        selector: 'settings-component',
        templateUrl: 'client/settings/settings.html',
        styleUrls: [
            'client/settings/settings.css',
        ],
        providers: [settings_service_1.SettingsService],
    }),
    __metadata("design:paramtypes", [settings_service_1.SettingsService, ng_bootstrap_1.NgbModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], SettingsComponent);
exports.SettingsComponent = SettingsComponent;
