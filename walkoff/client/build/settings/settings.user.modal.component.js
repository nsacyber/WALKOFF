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
var workingUser_1 = require("../models/workingUser");
var SettingsUserModalComponent = (function () {
    function SettingsUserModalComponent(settingsService, activeModal, toastyService, toastyConfig) {
        this.settingsService = settingsService;
        this.activeModal = activeModal;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.toastyConfig.theme = 'bootstrap';
    }
    SettingsUserModalComponent.prototype.ngOnInit = function () {
        this.roleSelectData = this.roles.map(function (role) {
            return { id: role.id.toString(), text: role.name };
        });
        this.roleSelectConfig = {
            width: '100%',
            placeholder: 'Select role(s)',
            multiple: true,
            allowClear: true,
            closeOnSelect: false,
        };
        this.roleSelectInitialValue = JSON.parse(JSON.stringify(this.workingUser.role_ids));
    };
    SettingsUserModalComponent.prototype.roleSelectChange = function ($event) {
        this.workingUser.role_ids = $event.value.map(function (id) { return +id; });
    };
    SettingsUserModalComponent.prototype.submit = function () {
        var _this = this;
        var validationMessage = this.validate();
        if (validationMessage) {
            this.toastyService.error(validationMessage);
            return;
        }
        var toSubmit = workingUser_1.WorkingUser.toUser(this.workingUser);
        delete toSubmit.roles;
        if (toSubmit.id) {
            this.settingsService
                .editUser(toSubmit)
                .then(function (user) { return _this.activeModal.close({
                user: user,
                isEdit: true,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
        else {
            this.settingsService
                .addUser(toSubmit)
                .then(function (user) { return _this.activeModal.close({
                user: user,
                isEdit: false,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
    };
    SettingsUserModalComponent.prototype.validate = function () {
        if (!this.workingUser) {
            return 'User is not specified.';
        }
        if (!this.workingUser.id && !this.workingUser.newPassword) {
            return 'You must specify a password.';
        }
        if (this.workingUser.confirmNewPassword !== this.workingUser.newPassword) {
            return 'Passwords do not match.';
        }
        return '';
    };
    return SettingsUserModalComponent;
}());
__decorate([
    core_1.Input(),
    __metadata("design:type", workingUser_1.WorkingUser)
], SettingsUserModalComponent.prototype, "workingUser", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], SettingsUserModalComponent.prototype, "title", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], SettingsUserModalComponent.prototype, "submitText", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], SettingsUserModalComponent.prototype, "roles", void 0);
SettingsUserModalComponent = __decorate([
    core_1.Component({
        selector: 'user-modal',
        templateUrl: 'client/settings/settings.user.modal.html',
        styleUrls: [
            'client/settings/settings.css',
        ],
        providers: [settings_service_1.SettingsService],
    }),
    __metadata("design:paramtypes", [settings_service_1.SettingsService, ng_bootstrap_1.NgbActiveModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], SettingsUserModalComponent);
exports.SettingsUserModalComponent = SettingsUserModalComponent;
