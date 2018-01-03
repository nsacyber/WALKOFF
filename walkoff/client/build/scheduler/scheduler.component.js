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
var scheduler_modal_component_1 = require("./scheduler.modal.component");
var scheduler_service_1 = require("./scheduler.service");
var SchedulerComponent = (function () {
    function SchedulerComponent(schedulerService, modalService, toastyService, toastyConfig) {
        var _this = this;
        this.schedulerService = schedulerService;
        this.modalService = modalService;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.scheduledTasks = [];
        this.displayScheduledTasks = [];
        this.availableWorkflows = [];
        this.filterQuery = new forms_1.FormControl();
        this.currentController = 'Default Controller';
        this.toastyConfig.theme = 'bootstrap';
        this.getSchedulerStatus();
        this.getWorkflowNames();
        this.getScheduledTasks();
        this.filterQuery
            .valueChanges
            .debounceTime(500)
            .subscribe(function (event) { return _this.filterScheduledTasks(); });
    }
    SchedulerComponent.prototype.filterScheduledTasks = function () {
        var searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';
        this.displayScheduledTasks = this.scheduledTasks.filter(function (s) {
            return (s.name.toLocaleLowerCase().includes(searchFilter) ||
                s.description.toString().includes(searchFilter));
        });
    };
    SchedulerComponent.prototype.getSchedulerStatus = function () {
        var _this = this;
        this.schedulerService
            .getSchedulerStatus()
            .then(function (schedulerStatus) { return _this.schedulerStatus = schedulerStatus; })
            .catch(function (e) { return _this.toastyService.error("Error retrieving scheduler status: " + e.message); });
    };
    SchedulerComponent.prototype.changeSchedulerStatus = function (status) {
        var _this = this;
        if (status === 'start' && this.schedulerStatus === 'paused') {
            status = 'resume';
        }
        this.schedulerService
            .changeSchedulerStatus(status)
            .then(function (newStatus) {
            if (newStatus) {
                _this.schedulerStatus = newStatus;
            }
        })
            .catch(function (e) { return _this.toastyService.error("Error changing scheduler status: " + e.message); });
    };
    SchedulerComponent.prototype.getScheduledTasks = function () {
        var _this = this;
        this.schedulerService
            .getScheduledTasks()
            .then(function (scheduledTasks) { return _this.displayScheduledTasks = _this.scheduledTasks = scheduledTasks; })
            .catch(function (e) { return _this.toastyService.error("Error retrieving scheduled tasks: " + e.message); });
    };
    SchedulerComponent.prototype.addScheduledTask = function () {
        var modalRef = this.modalService.open(scheduler_modal_component_1.SchedulerModalComponent, { size: 'lg' });
        modalRef.componentInstance.title = 'Schedule a New Task';
        modalRef.componentInstance.submitText = 'Add Scheduled Task';
        modalRef.componentInstance.availableWorkflows = this.availableWorkflows;
        this._handleModalClose(modalRef);
    };
    SchedulerComponent.prototype.editScheduledTask = function (task) {
        var modalRef = this.modalService.open(scheduler_modal_component_1.SchedulerModalComponent, { size: 'lg' });
        modalRef.componentInstance.title = "Edit Task " + task.name;
        modalRef.componentInstance.submitText = 'Save Changes';
        modalRef.componentInstance.availableWorkflows = this.availableWorkflows;
        modalRef.componentInstance.workingScheduledTask = _.cloneDeep(task);
        delete modalRef.componentInstance.workingScheduledTask.$$index;
        this._handleModalClose(modalRef);
    };
    SchedulerComponent.prototype.deleteScheduledTask = function (taskToDelete) {
        var _this = this;
        if (!confirm("Are you sure you want to delete the scheduled task \"" + taskToDelete.name + "\"?")) {
            return;
        }
        this.schedulerService
            .deleteScheduledTask(taskToDelete.id)
            .then(function () {
            _this.scheduledTasks = _.reject(_this.scheduledTasks, function (scheduledTask) { return scheduledTask.id === taskToDelete.id; });
            _this.filterScheduledTasks();
            _this.toastyService.success("Scheduled Task \"" + taskToDelete.name + "\" successfully deleted.");
        })
            .catch(function (e) { return _this.toastyService.error("Error deleting task: " + e.message); });
    };
    SchedulerComponent.prototype.changeScheduledTaskStatus = function (task, actionName) {
        var _this = this;
        var newStatus;
        switch (actionName) {
            case 'start':
                newStatus = 'running';
                break;
            case 'pause':
                newStatus = 'paused';
                break;
            case 'stop':
                newStatus = 'stopped';
                break;
            default:
                this.toastyService.error("Attempted to set an unknown status " + actionName);
                break;
        }
        if (!newStatus) {
            return;
        }
        this.schedulerService
            .changeScheduledTaskStatus(task.id, actionName)
            .then(function () {
            task.status = newStatus;
        })
            .catch(function (e) { return _this.toastyService.error("Error changing scheduler status: " + e.message); });
    };
    SchedulerComponent.prototype.getWorkflowNames = function () {
        var self = this;
        this.schedulerService
            .getPlaybooks()
            .then(function (playbooks) {
            playbooks.forEach(function (pb) {
                pb.workflows.forEach(function (w) {
                    self.availableWorkflows.push({
                        id: w.uid,
                        text: pb.name + " - " + w.name,
                    });
                });
            });
        });
    };
    SchedulerComponent.prototype.getRule = function (scheduledTask) {
        var rule = JSON.stringify(scheduledTask.task_trigger.args, null, 1);
        rule = rule.substr(1, rule.length - 2).replace(/"/g, '');
        return rule;
    };
    SchedulerComponent.prototype.getFriendlyWorkflows = function (scheduledTask) {
        if (!this.availableWorkflows || !scheduledTask.workflows || !scheduledTask.workflows.length) {
            return '';
        }
        return this.availableWorkflows.filter(function (workflow) {
            return scheduledTask.workflows.indexOf(workflow.id) >= 0;
        }).map(function (workflow) {
            return workflow.text;
        }).join(', ');
    };
    SchedulerComponent.prototype._handleModalClose = function (modalRef) {
        var _this = this;
        modalRef.result
            .then(function (result) {
            if (!result || !result.scheduledTask) {
                return;
            }
            if (result.isEdit) {
                var toUpdate = _.find(_this.scheduledTasks, function (st) { return st.id === result.scheduledTask.id; });
                Object.assign(toUpdate, result.scheduledTask);
                _this.filterScheduledTasks();
                _this.toastyService.success("Scheduled task \"" + result.scheduledTask.name + "\" successfully edited.");
            }
            else {
                _this.scheduledTasks.push(result.scheduledTask);
                _this.filterScheduledTasks();
                _this.toastyService.success("Scheduled task \"" + result.scheduledTask.name + "\" successfully added.");
            }
        }, function (error) { if (error) {
            _this.toastyService.error(error.message);
        } });
    };
    return SchedulerComponent;
}());
SchedulerComponent = __decorate([
    core_1.Component({
        selector: 'scheduler-component',
        templateUrl: 'client/scheduler/scheduler.html',
        styleUrls: [
            'client/scheduler/scheduler.css',
        ],
        encapsulation: core_1.ViewEncapsulation.None,
        providers: [scheduler_service_1.SchedulerService],
    }),
    __metadata("design:paramtypes", [scheduler_service_1.SchedulerService, ng_bootstrap_1.NgbModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], SchedulerComponent);
exports.SchedulerComponent = SchedulerComponent;
