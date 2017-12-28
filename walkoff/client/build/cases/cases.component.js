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
var cases_service_1 = require("./cases.service");
var cases_modal_component_1 = require("./cases.modal.component");
var case_1 = require("../models/case");
var types = ['playbook', 'workflow', 'action', 'branch', 'condition', 'transform'];
var childrenTypes = ['workflows', 'actions', 'branches', 'conditions', 'transforms'];
var CasesComponent = (function () {
    function CasesComponent(casesService, modalService, toastyService, toastyConfig) {
        var _this = this;
        this.casesService = casesService;
        this.modalService = modalService;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.cases = [];
        this.availableCases = [];
        this.availableSubscriptions = [];
        this.caseEvents = [];
        this.displayCases = [];
        this.displayCaseEvents = [];
        this.eventFilterQuery = new forms_1.FormControl();
        this.caseFilterQuery = new forms_1.FormControl();
        this.toastyConfig.theme = 'bootstrap';
        this.caseSelectConfig = {
            width: '100%',
            placeholder: 'Select a Case to view its Events',
        };
        this.getCases();
        this.getAvailableSubscriptions();
        this.getPlaybooks();
        this.eventFilterQuery
            .valueChanges
            .debounceTime(500)
            .subscribe(function (event) { return _this.filterEvents(); });
        this.caseFilterQuery
            .valueChanges
            .debounceTime(500)
            .subscribe(function (event) { return _this.filterCases(); });
    }
    CasesComponent.prototype.caseSelectChange = function ($event) {
        if (!$event.value || $event.value === '') {
            return;
        }
        this.getCaseEvents($event.value);
    };
    CasesComponent.prototype.filterEvents = function () {
        var searchFilter = this.eventFilterQuery.value ? this.eventFilterQuery.value.toLocaleLowerCase() : '';
        this.displayCaseEvents = this.caseEvents.filter(function (caseEvent) {
            return caseEvent.type.toLocaleLowerCase().includes(searchFilter) ||
                caseEvent.message.includes(searchFilter);
        });
    };
    CasesComponent.prototype.filterCases = function () {
        var searchFilter = this.caseFilterQuery.value ? this.caseFilterQuery.value.toLocaleLowerCase() : '';
        this.displayCases = this.cases.filter(function (c) {
            return c.name.toLocaleLowerCase().includes(searchFilter) ||
                c.note.includes(searchFilter);
        });
    };
    CasesComponent.prototype.getCases = function () {
        var _this = this;
        this.casesService
            .getCases()
            .then(function (cases) {
            _this.displayCases = _this.cases = cases;
            _this.availableCases = [{ id: '', text: '' }].concat(cases.map(function (c) { return ({ id: c.id.toString(), text: c.name }); }));
        })
            .catch(function (e) { return _this.toastyService.error("Error retrieving cases: " + e.message); });
    };
    CasesComponent.prototype.getCaseEvents = function (caseName) {
        var _this = this;
        this.casesService
            .getEventsForCase(caseName)
            .then(function (caseEvents) {
            _this.displayCaseEvents = _this.caseEvents = caseEvents;
            _this.filterEvents();
        })
            .catch(function (e) { return _this.toastyService.error("Error retrieving events: " + e.message); });
    };
    CasesComponent.prototype.addCase = function () {
        var modalRef = this.modalService.open(cases_modal_component_1.CasesModalComponent, { windowClass: 'casesModal' });
        modalRef.componentInstance.title = 'Add New Case';
        modalRef.componentInstance.submitText = 'Add Case';
        modalRef.componentInstance.workingCase = new case_1.Case();
        modalRef.componentInstance.availableSubscriptions = this.availableSubscriptions;
        modalRef.componentInstance.subscriptionTree = _.cloneDeep(this.subscriptionTree);
        this._handleModalClose(modalRef);
    };
    CasesComponent.prototype.editCase = function (caseToEdit) {
        var modalRef = this.modalService.open(cases_modal_component_1.CasesModalComponent, { windowClass: 'casesModal' });
        modalRef.componentInstance.title = "Edit Case: " + caseToEdit.name;
        modalRef.componentInstance.submitText = 'Save Changes';
        modalRef.componentInstance.workingCase = _.cloneDeep(caseToEdit);
        delete modalRef.componentInstance.workingCase.$$index;
        modalRef.componentInstance.availableSubscriptions = this.availableSubscriptions;
        modalRef.componentInstance.subscriptionTree = _.cloneDeep(this.subscriptionTree);
        this._handleModalClose(modalRef);
    };
    CasesComponent.prototype.deleteCase = function (caseToDelete) {
        var _this = this;
        if (!confirm('Are you sure you want to delete the case "' + caseToDelete.name +
            '"? This will also delete any associated events.')) {
            return;
        }
        this.casesService
            .deleteCase(caseToDelete.id)
            .then(function () {
            _this.cases = _.reject(_this.cases, function (c) { return c.id === caseToDelete.id; });
            _this.filterCases();
            _this.toastyService.success("Case \"" + caseToDelete.name + "\" successfully deleted.");
        })
            .catch(function (e) { return _this.toastyService.error(e.message); });
    };
    CasesComponent.prototype.getAvailableSubscriptions = function () {
        var _this = this;
        this.casesService
            .getAvailableSubscriptions()
            .then(function (availableSubscriptions) { return _this.availableSubscriptions = availableSubscriptions; })
            .catch(function (e) { return _this.toastyService.error("Error retrieving case subscriptions: " + e.message); });
    };
    CasesComponent.prototype.getPlaybooks = function () {
        var _this = this;
        this.casesService
            .getPlaybooks()
            .then(function (playbooks) { return _this.subscriptionTree = _this.convertPlaybooksToSubscriptionTree(playbooks); })
            .catch(function (e) { return _this.toastyService.error("Error retrieving subscription tree: " + e.message); });
    };
    CasesComponent.prototype.convertPlaybooksToSubscriptionTree = function (playbooks) {
        var self = this;
        var tree = { name: 'Controller', uid: 'controller', type: 'controller', children: [] };
        playbooks.forEach(function (p) {
            p.workflows.forEach(function (w) {
                w.actions.forEach(function (s) {
                    s.branches = [];
                });
                w.branches.forEach(function (ns) {
                    var matchingAction = w.actions.find(function (s) { return s.uid === ns.destination_uid; });
                    if (matchingAction) {
                        ns.name = matchingAction.name;
                    }
                    w.actions.find(function (s) { return s.uid === ns.source_uid; }).branches.push(ns);
                });
                delete w.branches;
            });
        });
        playbooks.forEach(function (p) {
            tree.children.push(self.getNodeRecursive(p, 0));
        });
        return tree;
    };
    CasesComponent.prototype.getNodeRecursive = function (target, typeIndex, prefix) {
        var self = this;
        var nodeName = '';
        if (prefix) {
            nodeName = prefix + ': ';
        }
        if (target.name) {
            nodeName += target.name;
        }
        else if (target.action_name) {
            nodeName += target.action_name;
        }
        else {
            nodeName = '(name unknown)';
        }
        var node = {
            name: nodeName,
            uid: target.uid ? target.uid : '',
            type: types[typeIndex],
            children: [],
        };
        var childType = childrenTypes[typeIndex];
        if (childType) {
            var childPrefix_1;
            switch (childType) {
                case 'actions':
                    childPrefix_1 = 'Action';
                    break;
                case 'branches':
                    childPrefix_1 = 'Branch';
                    break;
                case 'conditions':
                    childPrefix_1 = 'Condition';
                    break;
                case 'transforms':
                    childPrefix_1 = 'Transform';
                    break;
                default:
                    break;
            }
            target[childType].forEach(function (sub) {
                node.children.push(self.getNodeRecursive(sub, typeIndex + 1, childPrefix_1));
            });
        }
        if (!node.children.length) {
            delete node.children;
        }
        return node;
    };
    CasesComponent.prototype.getFriendlyArray = function (input) {
        return input.join(', ');
    };
    CasesComponent.prototype.getFriendlyObject = function (input) {
        var out = JSON.stringify(input, null, 1);
        out = out.substr(1, out.length - 2).replace(/"/g, '');
        return out;
    };
    CasesComponent.prototype._handleModalClose = function (modalRef) {
        var _this = this;
        modalRef.result
            .then(function (result) {
            if (!result || !result.case) {
                return;
            }
            if (result.isEdit) {
                var toUpdate = _.find(_this.cases, function (c) { return c.id === result.case.id; });
                Object.assign(toUpdate, result.case);
                _this.filterCases();
                _this.toastyService.success("Case \"" + result.case.name + "\" successfully edited.");
            }
            else {
                _this.cases.push(result.case);
                _this.filterCases();
                _this.toastyService.success("Case \"" + result.case.name + "\" successfully added.");
            }
        }, function (error) { if (error) {
            _this.toastyService.error(error.message);
        } });
    };
    return CasesComponent;
}());
CasesComponent = __decorate([
    core_1.Component({
        selector: 'cases-component',
        templateUrl: 'client/cases/cases.html',
        encapsulation: core_1.ViewEncapsulation.None,
        styleUrls: [
            'client/cases/cases.css',
        ],
        providers: [cases_service_1.CasesService],
    }),
    __metadata("design:paramtypes", [cases_service_1.CasesService, ng_bootstrap_1.NgbModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], CasesComponent);
exports.CasesComponent = CasesComponent;
