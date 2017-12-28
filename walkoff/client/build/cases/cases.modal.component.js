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
var d3 = require("d3");
var cases_service_1 = require("./cases.service");
var case_1 = require("../models/case");
var subscription_1 = require("../models/subscription");
var CasesModalComponent = (function () {
    function CasesModalComponent(casesService, activeModal, toastyService, toastyConfig) {
        this.casesService = casesService;
        this.activeModal = activeModal;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.availableSubscriptions = [];
        this.workingEvents = [];
        this.selectedNode = { name: '', uid: '', type: '' };
        this.toastyConfig.theme = 'bootstrap';
    }
    CasesModalComponent.prototype.ngOnInit = function () {
        var self = this;
        var uids = self.workingCase.subscriptions.map(function (s) { return s.uid; });
        var margin = { top: 20, right: 90, bottom: 30, left: 90 };
        var width = 1350 - margin.left - margin.right;
        var height = 500 - margin.top - margin.bottom;
        var svg = d3.select('svg#caseSubscriptionsTree')
            .attr('width', width + margin.right + margin.left)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', "translate(" + margin.left + "," + margin.top + ")");
        var i = 0;
        var duration = 400;
        var root;
        var treemap = d3.tree().size([height, width]);
        root = d3.hierarchy(self.subscriptionTree);
        root.x0 = height / 2;
        root.y0 = 0;
        if (uids.indexOf('controller') >= 0) {
            root.data._included = true;
        }
        root.children.forEach(checkInclusionAndCheckChildrenForExpansion);
        update(root);
        function checkInclusionAndCheckChildrenForExpansion(d) {
            if (uids.indexOf(d.data.uid) >= 0) {
                d.data._included = true;
            }
            var expanded = false;
            if (d.children) {
                d.children.forEach(function (child) {
                    expanded = checkInclusionAndCheckChildrenForExpansion(child) || expanded;
                });
            }
            if (!expanded && d.children) {
                d._children = d.children;
                d.children = null;
            }
            return d.data._included;
        }
        function update(source) {
            var treeData = treemap(root);
            var nodes = treeData.descendants();
            var links = treeData.descendants().slice(1);
            nodes.forEach(function (d) { return d.y = d.depth * 180; });
            var node = svg.selectAll('g.node')
                .data(nodes, function (d) { return d.id || (d.id = ++i); });
            var nodeEnter = node.enter().append('g')
                .classed('node', true)
                .classed('included', function (d) {
                return d.data._included;
            })
                .attr('transform', function (d) {
                return 'translate(' + source.y0 + ',' + source.x0 + ')';
            })
                .attr('id', function (d) { return "uid-" + d.data.uid; })
                .on('click', click)
                .on('dblclick', dblclick);
            nodeEnter.append('circle')
                .classed('node', true)
                .attr('r', 1e-6)
                .style('fill', function (d) {
                return d._children ? 'lightsteelblue' : '#fff';
            });
            nodeEnter.append('text')
                .attr('dy', '.35em')
                .attr('x', function (d) {
                return d.children || d._children ? -13 : 13;
            })
                .attr('text-anchor', function (d) {
                return d.children || d._children ? 'end' : 'start';
            })
                .text(function (d) { return d.data.name; });
            var nodeUpdate = nodeEnter.merge(node);
            nodeUpdate.transition()
                .duration(duration)
                .attr('transform', function (d) {
                return 'translate(' + d.y + ',' + d.x + ')';
            });
            nodeUpdate.select('circle.node')
                .attr('r', 10)
                .style('fill', function (d) {
                return d._children ? 'lightsteelblue' : '#fff';
            });
            var nodeExit = node.exit().transition()
                .duration(duration)
                .attr('transform', function (d) {
                return 'translate(' + source.y + ',' + source.x + ')';
            })
                .remove();
            nodeExit.select('circle')
                .attr('r', 1e-6);
            nodeExit.select('text')
                .style('fill-opacity', 1e-6);
            var link = svg.selectAll('path.link')
                .data(links, function (d) { return d.id; });
            var linkEnter = link.enter().insert('path', 'g')
                .classed('link', true)
                .attr('d', function (d) {
                var o = { x: source.x0, y: source.y0 };
                return diagonal(o, o);
            });
            var linkUpdate = linkEnter.merge(link);
            linkUpdate.transition()
                .duration(duration)
                .attr('d', function (d) { return diagonal(d, d.parent); });
            link.exit().transition()
                .duration(duration)
                .attr('d', function (d) {
                var o = { x: source.x, y: source.y };
                return diagonal(o, o);
            })
                .remove();
            nodes.forEach(function (d) {
                d.x0 = d.x;
                d.y0 = d.y;
            });
            function diagonal(s, d) {
                var path = "M " + s.y + " " + s.x + "\n\t\t\t\t\tC " + (s.y + d.y) / 2 + " " + s.x + ",\n\t\t\t\t\t" + (s.y + d.y) / 2 + " " + d.x + ",\n\t\t\t\t\t" + d.y + " " + d.x;
                return path;
            }
            function dblclick(d) {
                if (d.children) {
                    d._children = d.children;
                    d.children = null;
                }
                else {
                    d.children = d._children;
                    d._children = null;
                }
                update(d);
            }
            function click(d) {
                if (!d.data.type) {
                    return;
                }
                self.selectedNode = { name: d.data.name, uid: d.data.uid, type: d.data.type };
                var availableEvents = self.availableSubscriptions.find(function (a) {
                    return d.data.type === a.type;
                }).events;
                var subscription = self.workingCase.subscriptions.find(function (s) {
                    return d.data.uid === s.uid;
                });
                var subscriptionEvents = subscription ? subscription.events : [];
                self.workingEvents = [];
                availableEvents.forEach(function (event) {
                    self.workingEvents.push({
                        name: event,
                        isChecked: subscriptionEvents.indexOf(event) > -1,
                    });
                });
                d3.selectAll('g.node.highlighted')
                    .classed('highlighted', false);
                d3.select(this)
                    .classed('highlighted', true);
            }
        }
    };
    CasesModalComponent.prototype.handleEventSelectionChange = function (event, isChecked) {
        var self = this;
        if (!self.selectedNode.name) {
            console.error('Attempted to select events without a node selected.');
            return;
        }
        event.isChecked = isChecked;
        var matchingSubscription = self.workingCase.subscriptions.find(function (s) {
            return s.uid === self.selectedNode.uid;
        });
        if (!matchingSubscription) {
            matchingSubscription = new subscription_1.Subscription();
            matchingSubscription.uid = self.selectedNode.uid;
            self.workingCase.subscriptions.push(matchingSubscription);
            d3.select('svg#caseSubscriptionsTree').select("g.node#uid-" + self.selectedNode.uid)
                .classed('included', true)
                .datum(function (d) {
                d.data._included = true;
                return d;
            });
        }
        matchingSubscription.events = self.workingEvents.filter(function (we) {
            return we.isChecked;
        }).map(function (we) {
            return we.name;
        });
        if (!matchingSubscription.events.length) {
            var indexToDelete = self.workingCase.subscriptions.indexOf(matchingSubscription);
            self.workingCase.subscriptions.splice(indexToDelete, 1);
            d3.select('svg#caseSubscriptionsTree').select("g.node#uid-" + self.selectedNode.uid)
                .classed('included', false)
                .datum(function (d) {
                d.data._included = false;
                return d;
            });
        }
    };
    CasesModalComponent.prototype.submit = function () {
        var _this = this;
        var validationMessage = this.validate();
        if (validationMessage) {
            this.toastyService.error(validationMessage);
            return;
        }
        if (this.workingCase.id) {
            this.casesService
                .editCase(this.workingCase)
                .then(function (c) { return _this.activeModal.close({
                case: c,
                isEdit: true,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
        else {
            this.casesService
                .addCase(this.workingCase)
                .then(function (c) { return _this.activeModal.close({
                case: c,
                isEdit: false,
            }); })
                .catch(function (e) { return _this.toastyService.error(e.message); });
        }
    };
    CasesModalComponent.prototype.validate = function () {
        return '';
    };
    return CasesModalComponent;
}());
__decorate([
    core_1.Input(),
    __metadata("design:type", case_1.Case)
], CasesModalComponent.prototype, "workingCase", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], CasesModalComponent.prototype, "title", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", String)
], CasesModalComponent.prototype, "submitText", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], CasesModalComponent.prototype, "availableSubscriptions", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Object)
], CasesModalComponent.prototype, "subscriptionTree", void 0);
__decorate([
    core_1.Input(),
    __metadata("design:type", Array)
], CasesModalComponent.prototype, "workingEvents", void 0);
CasesModalComponent = __decorate([
    core_1.Component({
        encapsulation: core_1.ViewEncapsulation.None,
        selector: 'case-modal',
        templateUrl: 'client/cases/cases.modal.html',
        styleUrls: [
            'client/cases/cases.modal.css',
        ],
        providers: [cases_service_1.CasesService],
    }),
    __metadata("design:paramtypes", [cases_service_1.CasesService, ng_bootstrap_1.NgbActiveModal,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig])
], CasesModalComponent);
exports.CasesModalComponent = CasesModalComponent;
