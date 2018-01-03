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
var devices_modal_component_1 = require("./devices.modal.component");
var devices_service_1 = require("./devices.service");
var device_1 = require("../models/device");
var DevicesComponent = (function () {
    function DevicesComponent(devicesService, modalService, toastyService, toastyConfig) {
        var _this = this;
        this.devicesService = devicesService;
        this.modalService = modalService;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.devices = [];
        this.displayDevices = [];
        this.appNames = [];
        this.availableApps = [];
        this.appApis = [];
        this.selectedApps = [];
        this.filterQuery = new forms_1.FormControl();
        this.toastyConfig.theme = 'bootstrap';
        this.appSelectConfig = {
            width: '100%',
            multiple: true,
            allowClear: true,
            placeholder: 'Filter by app(s)...',
            closeOnSelect: false,
        };
        this.getDevices();
        this.getDeviceApis();
        this.filterQuery
            .valueChanges
            .debounceTime(500)
            .subscribe(function (event) { return _this.filterDevices(); });
    }
    DevicesComponent.prototype.appSelectChange = function ($event) {
        this.selectedApps = $event.value;
        this.filterDevices();
    };
    DevicesComponent.prototype.filterDevices = function () {
        var _this = this;
        var searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';
        this.displayDevices = this.devices.filter(function (device) {
            return (device.name.toLocaleLowerCase().includes(searchFilter) ||
                device.app_name.toLocaleLowerCase().includes(searchFilter) ||
                device.ip.includes(searchFilter) ||
                device.port.toString().includes(searchFilter)) &&
                (_this.selectedApps.length ? _this.selectedApps.indexOf(device.app_name) > -1 : true);
        });
    };
    DevicesComponent.prototype.getDevices = function () {
        var _this = this;
        this.devicesService
            .getDevices()
            .then(function (devices) { return _this.displayDevices = _this.devices = devices; })
            .catch(function (e) { return _this.toastyService.error("Error retrieving devices: " + e.message); });
    };
    DevicesComponent.prototype.addDevice = function () {
        var modalRef = this.modalService.open(devices_modal_component_1.DevicesModalComponent);
        modalRef.componentInstance.title = 'Add New Device';
        modalRef.componentInstance.submitText = 'Add Device';
        modalRef.componentInstance.appNames = this.appNames;
        modalRef.componentInstance.appApis = this.appApis;
        this._handleModalClose(modalRef);
    };
    DevicesComponent.prototype.editDevice = function (device) {
        var modalRef = this.modalService.open(devices_modal_component_1.DevicesModalComponent);
        modalRef.componentInstance.title = "Edit Device " + device.name;
        modalRef.componentInstance.submitText = 'Save Changes';
        modalRef.componentInstance.appNames = this.appNames;
        modalRef.componentInstance.appApis = this.appApis;
        modalRef.componentInstance.workingDevice = device_1.Device.toWorkingDevice(device);
        this._handleModalClose(modalRef);
    };
    DevicesComponent.prototype.deleteDevice = function (deviceToDelete) {
        var _this = this;
        if (!confirm("Are you sure you want to delete the device \"" + deviceToDelete.name + "\"?")) {
            return;
        }
        this.devicesService
            .deleteDevice(deviceToDelete.id)
            .then(function () {
            _this.devices = _.reject(_this.devices, function (device) { return device.id === deviceToDelete.id; });
            _this.filterDevices();
            _this.toastyService.success("Device \"" + deviceToDelete.name + "\" successfully deleted.");
        })
            .catch(function (e) { return _this.toastyService.error("Error deleting device: " + e.message); });
    };
    DevicesComponent.prototype.getDeviceApis = function () {
        var _this = this;
        this.devicesService
            .getDeviceApis()
            .then(function (appApis) {
            _this.appApis = appApis;
            _this.appNames = appApis.map(function (a) { return a.name; });
            _this.availableApps = _this.appNames.map(function (appName) { return ({ id: appName, text: appName }); });
        })
            .catch(function (e) { return _this.toastyService.error("Error retrieving device types: " + e.message); });
    };
    DevicesComponent.prototype.getCustomFields = function (device) {
        var obj = {};
        device.fields.forEach(function (element) {
            if (element.value) {
                obj[element.name] = element.value;
            }
        });
        var out = JSON.stringify(obj, null, 1);
        out = out.substr(1, out.length - 2).replace(/"/g, '');
        return out;
    };
    DevicesComponent.prototype._handleModalClose = function (modalRef) {
        var _this = this;
        modalRef.result
            .then(function (result) {
            if (!result || !result.device) {
                return;
            }
            if (result.isEdit) {
                var toUpdate = _.find(_this.devices, function (d) { return d.id === result.device.id; });
                Object.assign(toUpdate, result.device);
                _this.filterDevices();
                _this.toastyService.success("Device \"" + result.device.name + "\" successfully edited.");
            }
            else {
                _this.devices.push(result.device);
                _this.filterDevices();
                _this.toastyService.success("Device \"" + result.device.name + "\" successfully added.");
            }
        }, function (error) { if (error) {
            _this.toastyService.error(error.message);
        } });
    };
    return DevicesComponent;
}());
DevicesComponent = __decorate([
    core_1.Component({
        selector: 'devices-component',
        templateUrl: 'client/devices/devices.html',
        styleUrls: [
            'client/devices/devices.css',
        ],
        encapsulation: core_1.ViewEncapsulation.None,
        providers: [devices_service_1.DevicesService],
    }),
    __metadata("design:paramtypes", [devices_service_1.DevicesService, ng_bootstrap_1.NgbModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], DevicesComponent);
exports.DevicesComponent = DevicesComponent;
