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
var devices_service_1 = require("./devices.service");
var workingDevice_1 = require("../models/workingDevice");
var DevicesModalComponent = (function () {
    function DevicesModalComponent(devicesService, activeModal, toastyService, toastyConfig, cdr) {
        this.devicesService = devicesService;
        this.activeModal = activeModal;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.cdr = cdr;
        this.workingDevice = new workingDevice_1.WorkingDevice();
        this.appNames = [];
        this.appApis = [];
        this.deviceTypesForApp = [];
        this.deviceTypeFields = {};
        this.validationErrors = {};
        this.encryptedConfirmFields = {};
        this.encryptedFieldsToBeCleared = {};
        this.toastyConfig.theme = 'bootstrap';
    }
    DevicesModalComponent.prototype.ngAfterViewInit = function () {
        var _this = this;
        if (this.workingDevice.app_name) {
            this.deviceTypesForApp = this.appApis.find(function (app) { return app.name === _this.workingDevice.app_name; }).device_apis;
        }
        this.cdr.detectChanges();
        if (this.workingDevice.type) {
            this.deviceTypeFields[this.workingDevice.type] = this.workingDevice.fields;
            this.typeRef.nativeElement.value = this.workingDevice.type;
            this.handleDeviceTypeSelection(null, this.workingDevice.type);
        }
        this.cdr.detectChanges();
    };
    DevicesModalComponent.prototype.handleAppSelection = function (event, appName) {
        this.workingDevice.app_name = appName;
        this.deviceTypesForApp = this.appApis.find(function (a) { return a.name === appName; }).device_apis;
        if (this.selectedDeviceType) {
            this._clearDeviceTypeData();
        }
    };
    DevicesModalComponent.prototype.handleDeviceTypeSelection = function (event, deviceType) {
        var _this = this;
        if (!deviceType) {
            this._clearDeviceTypeData();
            return;
        }
        this.selectedDeviceType = this.appApis.find(function (a) { return a.name === _this.workingDevice.app_name; })
            .device_apis.find(function (d) { return d.name === deviceType; });
        this.workingDevice.type = deviceType;
        this.workingDevice.fields =
            this.deviceTypeFields[deviceType] =
                this.deviceTypeFields[deviceType] || this._getDefaultValues(this.selectedDeviceType);
        this._getEncryptedConfirmFields(this.selectedDeviceType);
        this.validationErrors = {};
    };
    DevicesModalComponent.prototype.handleEncryptedFieldClear = function (fieldName, isChecked) {
        this.encryptedFieldsToBeCleared[fieldName] = isChecked;
    };
    DevicesModalComponent.prototype.submit = function () {
        var _this = this;
        if (!this.validate()) {
            return;
        }
        var toSubmit = workingDevice_1.WorkingDevice.toDevice(this.workingDevice);
        if (this.workingDevice.id) {
            var self_1 = this;
            toSubmit.fields.forEach(function (field, index, array) {
                var ftype = self_1.selectedDeviceType.fields.find(function (ft) { return ft.name === field.name; });
                if (!ftype.encrypted) {
                    return;
                }
                if (self_1.encryptedFieldsToBeCleared[field.name]) {
                    field.value = '';
                }
                else if ((typeof (field.value) === 'string' && !field.value.trim()) ||
                    (typeof (field.value) === 'number' && !field.value)) {
                    array.splice(index, 1);
                }
            });
            this.devicesService
                .editDevice(toSubmit)
                .then(function (device) { return _this.activeModal.close({
                device: device,
                isEdit: true,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
        else {
            this.devicesService
                .addDevice(toSubmit)
                .then(function (device) { return _this.activeModal.close({
                device: device,
                isEdit: false,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
    };
    DevicesModalComponent.prototype.isBasicInfoValid = function () {
        if (this.workingDevice.name && this.workingDevice.name.trim() &&
            this.workingDevice.app_name && this.workingDevice.type) {
            return true;
        }
        return false;
    };
    DevicesModalComponent.prototype.validate = function () {
        var _this = this;
        var self = this;
        this.validationErrors = {};
        var inputs = this.workingDevice.fields;
        Object.keys(inputs).forEach(function (key) {
            if (typeof (inputs[key]) === 'string') {
                inputs[key] = inputs[key].trim();
                if (self.encryptedConfirmFields[key]) {
                    self.encryptedConfirmFields[key] = self.encryptedConfirmFields[key].trim();
                }
            }
        });
        this.selectedDeviceType.fields.forEach(function (field) {
            if (field.required) {
                if (inputs[field.name] == null ||
                    (typeof inputs[field.name] === 'string' && !inputs[field.name]) ||
                    (typeof inputs[field.name] === 'number' && inputs[field.name] === null)) {
                    _this.validationErrors[field.name] = "You must enter a value for " + field.name + ".";
                    return;
                }
            }
            switch (field.schema.type) {
                case 'string':
                    if (inputs[field.name] == null) {
                        inputs[field.name] = '';
                    }
                    if (field.encrypted &&
                        !_this.encryptedFieldsToBeCleared[field.name] &&
                        _this.encryptedConfirmFields[field.name] !== inputs[field.name]) {
                        _this._concatValidationMessage(field.name, "The values for " + field.name + " do not match.");
                    }
                    if (field.schema.enum) {
                        var enumArray = field.schema.enum.slice(0);
                        if (!field.required) {
                            enumArray.push('');
                        }
                        if (enumArray.indexOf(inputs[field.name]) < 0) {
                            _this._concatValidationMessage(field.name, 'You must select a value from the list.');
                        }
                    }
                    if (!inputs[field.name]) {
                        break;
                    }
                    if (field.schema.minLength !== undefined && inputs[field.name].length < field.schema.minLength) {
                        _this._concatValidationMessage(field.name, "Must be at least " + field.schema.minLength + " characters.");
                    }
                    if (field.schema.maxLength !== undefined && inputs[field.name].length > field.schema.maxLength) {
                        _this._concatValidationMessage(field.name, "Must be at most " + field.schema.minLength + " characters.");
                    }
                    if (field.schema.pattern && !new RegExp(field.schema.pattern).test(inputs[field.name])) {
                        _this._concatValidationMessage(field.name, "Input must match a given pattern: " + field.schema.pattern + ".");
                    }
                    break;
                case 'number':
                case 'integer':
                    if (inputs[field.name] == null) {
                        break;
                    }
                    var min = _this.getMin(field.schema);
                    var max = _this.getMax(field.schema);
                    if (min !== null && inputs[field.name] < min) {
                        _this._concatValidationMessage(field.name, "The minimum value is " + min + ".");
                    }
                    if (max !== null && inputs[field.name] > max) {
                        _this._concatValidationMessage(field.name, "The maximum value is " + max + ".");
                    }
                    if (field.schema.multipleOf !== undefined && inputs[field.name] % field.schema.multipleOf) {
                        _this._concatValidationMessage(field.name, "The value must be a multiple of " + field.schema.multipleOf + ".");
                    }
                    break;
                case 'boolean':
                    inputs[field.name] = inputs[field.name] || false;
                    break;
                default:
                    _this._concatValidationMessage(field.name, "The type specified for field " + field.name + " is invalid.");
                    break;
            }
        });
        if (Object.keys(this.validationErrors).length) {
            return false;
        }
        return true;
    };
    DevicesModalComponent.prototype.getMin = function (schema) {
        if (schema.minimum === undefined) {
            return null;
        }
        if (schema.exclusiveMinimum) {
            return schema.minimum + 1;
        }
        return schema.minimum;
    };
    DevicesModalComponent.prototype.getMax = function (schema) {
        if (schema.maximum === undefined) {
            return null;
        }
        if (schema.exclusiveMaximum) {
            return schema.maximum - 1;
        }
        return schema.maximum;
    };
    DevicesModalComponent.prototype._getEncryptedConfirmFields = function (deviceType) {
        var _this = this;
        this.encryptedConfirmFields = {};
        deviceType.fields.forEach(function (field) {
            if (field.encrypted) {
                _this.encryptedConfirmFields[field.name] = '';
            }
        });
    };
    DevicesModalComponent.prototype._getDefaultValues = function (deviceApi) {
        var out = {};
        deviceApi.fields.forEach(function (field) {
            if (field.schema.default) {
                out[field.name] = field.schema.default;
            }
            else {
                out[field.name] = null;
            }
        });
        return out;
    };
    DevicesModalComponent.prototype._clearDeviceTypeData = function () {
        this.selectedDeviceType = null;
        this.workingDevice.type = null;
        this.workingDevice.fields = null;
        this.validationErrors = {};
        this.encryptedConfirmFields = {};
    };
    DevicesModalComponent.prototype._concatValidationMessage = function (field, message) {
        if (this.validationErrors[field]) {
            this.validationErrors[field] += '\n' + message;
        }
        else {
            this.validationErrors[field] = message;
        }
    };
    return DevicesModalComponent;
}());
__decorate([
    core_1.Input(),
    __metadata("design:type", workingDevice_1.WorkingDevice)
], DevicesModalComponent.prototype, "workingDevice", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], DevicesModalComponent.prototype, "title", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], DevicesModalComponent.prototype, "submitText", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], DevicesModalComponent.prototype, "appNames", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], DevicesModalComponent.prototype, "appApis", void 0);
__decorate([
    core_1.ViewChild('typeRef'),
    __metadata("design:type", core_1.ElementRef)
], DevicesModalComponent.prototype, "typeRef", void 0);
DevicesModalComponent = __decorate([
    core_1.Component({
        selector: 'device-modal',
        templateUrl: 'client/devices/devices.modal.html',
        styleUrls: [
            'client/devices/devices.css',
        ],
        providers: [devices_service_1.DevicesService],
    }),
    __metadata("design:paramtypes", [devices_service_1.DevicesService, ng_bootstrap_1.NgbActiveModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig, core_1.ChangeDetectorRef])
], DevicesModalComponent);
exports.DevicesModalComponent = DevicesModalComponent;
