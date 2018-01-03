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
var moment = require("moment");
var scheduler_service_1 = require("./scheduler.service");
var scheduledTask_1 = require("../models/scheduledTask");
var scheduledTaskCron_1 = require("../models/scheduledTaskCron");
var scheduledTaskInterval_1 = require("../models/scheduledTaskInterval");
var scheduledTaskDate_1 = require("../models/scheduledTaskDate");
var SchedulerModalComponent = (function () {
    function SchedulerModalComponent(schedulerService, activeModal, toastyService, toastyConfig) {
        this.schedulerService = schedulerService;
        this.activeModal = activeModal;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.workingScheduledTask = new scheduledTask_1.ScheduledTask();
        this.availableWorkflows = [];
        this.scheduledItemTriggerTypes = ['date', 'interval', 'cron'];
        this.cron = new scheduledTaskCron_1.ScheduledTaskCron();
        this.interval = new scheduledTaskInterval_1.ScheduledTaskInterval();
        this.date = new scheduledTaskDate_1.ScheduledTaskDate();
        this.toastyConfig.theme = 'bootstrap';
        this.workflowSelectConfig = {
            width: '100%',
            multiple: true,
            allowClear: true,
            placeholder: 'Select workflow(s) to run...',
            closeOnSelect: false,
        };
    }
    SchedulerModalComponent.prototype.submit = function () {
        var _this = this;
        var validationMessage = this.validate();
        if (validationMessage) {
            this.toastyService.error(validationMessage);
            return;
        }
        this.convertStringsToInt(this.workingScheduledTask.task_trigger.args);
        if (this.workingScheduledTask.id) {
            this.schedulerService
                .editScheduledTask(this.workingScheduledTask)
                .then(function (scheduledTask) { return _this.activeModal.close({
                scheduledTask: scheduledTask,
                isEdit: true,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
        else {
            this.schedulerService
                .addScheduledTask(this.workingScheduledTask)
                .then(function (scheduledTask) { return _this.activeModal.close({
                scheduledTask: scheduledTask,
                isEdit: false,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
    };
    SchedulerModalComponent.prototype.validate = function () {
        if (!this.workingScheduledTask.name) {
            return 'A name is required.';
        }
        if (!this.workingScheduledTask.workflows || !this.workingScheduledTask.workflows.length) {
            return 'Please specify at least one workflow to be run.';
        }
        var args = this.workingScheduledTask.task_trigger.args;
        if (!args) {
            return 'Please select a type and fill out the trigger parameters.';
        }
        if (!(args.start_date || args.run_date)) {
            return 'A start date is required.';
        }
        if (this.workingScheduledTask.task_trigger.type === 'interval' ||
            this.workingScheduledTask.task_trigger.type === 'cron') {
            var startDate = +args.start_date;
            var endDate = +args.end_date;
            if (startDate > endDate) {
                return 'The end date cannot be before the start date.';
            }
        }
        if (this.workingScheduledTask.task_trigger.type === 'interval') {
            if (!(args.weeks || args.days || args.hours || args.minutes || args.seconds)) {
                return 'You must specify some interval of time for the actions to occur.';
            }
        }
        if (this.workingScheduledTask.task_trigger.type === 'cron') {
            if (!(args.year || args.month || args.day || args.week ||
                args.day_of_week || args.hour || args.minute || args.second)) {
                return 'You must specify some cron parameters for the actions to occur.';
            }
        }
        return '';
    };
    SchedulerModalComponent.prototype.changeType = function (e) {
        switch (e) {
            case 'cron':
                this.workingScheduledTask.task_trigger.args = this.cron;
                break;
            case 'interval':
                this.workingScheduledTask.task_trigger.args = this.interval;
                break;
            case 'date':
                this.workingScheduledTask.task_trigger.args = this.date;
                break;
            default:
                this.workingScheduledTask.task_trigger.args = null;
                break;
        }
    };
    SchedulerModalComponent.prototype.workflowsSelectChanged = function (e) {
        this.workingScheduledTask.workflows = e.value;
    };
    SchedulerModalComponent.prototype.getToday = function () {
        return moment().format('YYYY-MM-DD');
    };
    SchedulerModalComponent.prototype.convertStringsToInt = function (args) {
        if (typeof (args) !== 'object') {
            return;
        }
        for (var _i = 0, _a = Object.entries(args); _i < _a.length; _i++) {
            var _b = _a[_i], key = _b[0], value = _b[1];
            var newVal = +value;
            if (typeof (value) !== 'string') {
                return;
            }
            args[key] = newVal;
        }
    };
    return SchedulerModalComponent;
}());
__decorate([
    core_1.Input(),
    __metadata("design:type", scheduledTask_1.ScheduledTask)
], SchedulerModalComponent.prototype, "workingScheduledTask", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], SchedulerModalComponent.prototype, "title", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], SchedulerModalComponent.prototype, "submitText", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], SchedulerModalComponent.prototype, "availableWorkflows", void 0);
SchedulerModalComponent = __decorate([
    core_1.Component({
        selector: 'scheduler-modal',
        templateUrl: 'client/scheduler/scheduler.modal.html',
        styleUrls: [
            'client/scheduler/scheduler.css',
        ],
        providers: [scheduler_service_1.SchedulerService],
    }),
    __metadata("design:paramtypes", [scheduler_service_1.SchedulerService, ng_bootstrap_1.NgbActiveModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], SchedulerModalComponent);
exports.SchedulerModalComponent = SchedulerModalComponent;
