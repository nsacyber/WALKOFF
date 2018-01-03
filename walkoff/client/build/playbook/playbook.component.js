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
var ng2_toasty_1 = require("ng2-toasty");
var angular2_uuid_1 = require("angular2-uuid");
var ngx_datatable_1 = require("@swimlane/ngx-datatable");
var playbook_service_1 = require("./playbook.service");
var auth_service_1 = require("../auth/auth.service");
var action_1 = require("../models/playbook/action");
var PlaybookComponent = (function () {
    function PlaybookComponent(playbookService, authService, toastyService, toastyConfig, cdr) {
        var _this = this;
        this.playbookService = playbookService;
        this.authService = authService;
        this.toastyService = toastyService;
        this.toastyConfig = toastyConfig;
        this.cdr = cdr;
        this.devices = [];
        this.relevantDevices = [];
        this.playbooks = [];
        this.appApis = [];
        this.offset = { x: -330, y: -170 };
        this.workflowResults = [];
        this.waitingOnData = false;
        this.modalParams = {
            title: '',
            submitText: '',
            shouldShowPlaybook: false,
            shouldShowExistingPlaybooks: false,
            selectedPlaybook: '',
            newPlaybook: '',
            shouldShowWorkflow: false,
            newWorkflow: '',
            submit: (function () { return null; }),
        };
        this.toastyConfig.theme = 'bootstrap';
        this.playbookService.getDevices().then(function (devices) { return _this.devices = devices; });
        this.playbookService.getApis().then(function (appApis) { return _this.appApis = appApis.sort(function (a, b) { return a.name > b.name ? 1 : -1; }); });
        this.getWorkflowResultsSSE();
        this.getPlaybooksWithWorkflows();
        this._addCytoscapeEventBindings();
    }
    PlaybookComponent.prototype.ngAfterViewChecked = function () {
        if (this.workflowResultsTable && this.workflowResultsTable.recalculate &&
            (this.workflowResultsContainer.nativeElement.clientWidth !== this.executionResultsComponentWidth)) {
            this.executionResultsComponentWidth = this.workflowResultsContainer.nativeElement.clientWidth;
            this.workflowResultsTable.recalculate();
            this.cdr.detectChanges();
        }
    };
    PlaybookComponent.prototype.getWorkflowResultsSSE = function () {
        var _this = this;
        this.authService.getAccessTokenRefreshed()
            .then(function (authToken) {
            var self = _this;
            var eventSource = new window.EventSource('api/workflowresults/stream?access_token=' + authToken);
            function eventHandler(message) {
                var workflowResult = JSON.parse(message.data);
                if (self.cy) {
                    var matchingNode = self.cy.elements("node[uid=\"" + workflowResult.action_uid + "\"]");
                    if (message.type === 'action_success') {
                        matchingNode.addClass('good-highlighted');
                    }
                    else {
                        matchingNode.addClass('bad-highlighted');
                    }
                }
                self.workflowResults.push(workflowResult);
                self.workflowResults = self.workflowResults.slice();
            }
            eventSource.addEventListener('action_success', eventHandler);
            eventSource.addEventListener('action_error', eventHandler);
            eventSource.addEventListener('error', function (err) {
                console.error(err);
            });
        });
    };
    PlaybookComponent.prototype.executeWorkflow = function () {
        var _this = this;
        this.clearExecutionHighlighting();
        this.playbookService.executeWorkflow(this.currentPlaybook, this.currentWorkflow)
            .then(function () { return _this.toastyService.success("Starting execution of " + _this.currentPlaybook + " - " + _this.currentWorkflow + "."); })
            .catch(function (e) { return _this.toastyService
            .error("Error starting execution of " + _this.currentPlaybook + " - " + _this.currentWorkflow + ": " + e.message); });
    };
    PlaybookComponent.prototype.loadWorkflow = function (playbookName, workflowName) {
        var _this = this;
        var self = this;
        this.playbookService.loadWorkflow(playbookName, workflowName)
            .then(function (workflow) {
            _this.currentPlaybook = playbookName;
            _this.currentWorkflow = workflowName;
            _this.loadedWorkflow = workflow;
            if (!_this.loadedWorkflow.actions) {
                _this.loadedWorkflow.actions = [];
            }
            _this.loadedWorkflow.actions.forEach(function (s) {
                s.arguments.forEach(function (i) {
                    if (i.selection && Array.isArray(i.selection)) {
                        i.selection = i.selection.join('.');
                    }
                });
            });
            _this.cy = cytoscape({
                container: document.getElementById('cy'),
                boxSelectionEnabled: false,
                autounselectify: false,
                wheelSensitivity: 0.1,
                layout: { name: 'preset' },
                style: [
                    {
                        selector: 'node',
                        css: {
                            'content': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'shape': 'roundrectangle',
                            'background-color': '#bbb',
                            'selection-box-color': 'red',
                            'font-family': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif, sans-serif',
                            'font-weight': 'lighter',
                            'font-size': '15px',
                            'width': '40',
                            'height': '40',
                        },
                    },
                    {
                        selector: 'node[type="action"]',
                        css: {
                            'background-color': '#bbb',
                        },
                    },
                    {
                        selector: 'node[type="eventAction"]',
                        css: {
                            'shape': 'star',
                            'background-color': '#edbd21',
                        },
                    },
                    {
                        selector: 'node[?isStartNode]',
                        css: {
                            'border-width': '2px',
                            'border-color': '#991818',
                        },
                    },
                    {
                        selector: 'node:selected',
                        css: {
                            'background-color': '#77b0d0',
                        },
                    },
                    {
                        selector: '.good-highlighted',
                        css: {
                            'background-color': '#399645',
                            'transition-property': 'background-color',
                            'transition-duration': '0.5s',
                        },
                    },
                    {
                        selector: '.bad-highlighted',
                        css: {
                            'background-color': '#8e3530',
                            'transition-property': 'background-color',
                            'transition-duration': '0.5s',
                        },
                    },
                    {
                        selector: '$node > node',
                        css: {
                            'padding-top': '10px',
                            'padding-left': '10px',
                            'padding-bottom': '10px',
                            'padding-right': '10px',
                            'text-valign': 'top',
                            'text-halign': 'center',
                        },
                    },
                    {
                        selector: 'edge',
                        css: {
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                        },
                    },
                ],
            });
            _this.ur = _this.cy.undoRedo({});
            _this.cy.panzoom({});
            _this.cy.edgehandles({
                preview: false,
                toggleOffOnLeave: true,
                complete: function (sourceNode, targetNodes, addedEntities) {
                    if (!self.loadedWorkflow.branches) {
                        self.loadedWorkflow.branches = [];
                    }
                    var _loop_1 = function (i) {
                        var uid = addedEntities[i].data('id');
                        var sourceUid = sourceNode.data('uid');
                        var destinationUid = targetNodes[i].data('uid');
                        addedEntities[i].data({
                            uid: uid,
                            temp: true,
                        });
                        if (self.loadedWorkflow.branches
                            .find(function (ns) { return ns.source_uid === sourceUid && ns.destination_uid === destinationUid; })) {
                            self.cy.remove(addedEntities);
                            return { value: void 0 };
                        }
                        var sourceAction = self.loadedWorkflow.actions.find(function (a) { return a.uid === sourceUid; });
                        var sourceActionApi = self._getAction(sourceAction.app_name, sourceAction.action_name);
                        var default_status = '';
                        if (sourceActionApi.default_return) {
                            default_status = sourceActionApi.default_return;
                        }
                        else if (sourceActionApi.returns.length) {
                            default_status = sourceActionApi.returns[0].status;
                        }
                        self.loadedWorkflow.branches.push({
                            uid: uid,
                            source_uid: sourceUid,
                            destination_uid: destinationUid,
                            status: default_status,
                            priority: 1,
                            conditions: [],
                        });
                    };
                    for (var i = 0; i < targetNodes.length; i++) {
                        var state_1 = _loop_1(i);
                        if (typeof state_1 === "object")
                            return state_1.value;
                    }
                    self.cy.remove(addedEntities);
                    addedEntities.forEach(function (ae) { return ae.data('temp', false); });
                    self.ur.do('add', addedEntities);
                },
            });
            _this.cy.clipboard();
            _this.cy.gridGuide({
                snapToGridDuringDrag: true,
                zoomDash: true,
                panGrid: true,
                centerToEdgeAlignment: true,
                distributionGuidelines: true,
                geometricGuideline: true,
                guidelinesStackOrder: 4,
                guidelinesTolerance: 2.00,
                guidelinesStyle: {
                    strokeStyle: '#8b7d6b',
                    geometricGuidelineRange: 400,
                    range: 100,
                    minDistRange: 10,
                    distGuidelineOffset: 10,
                    horizontalDistColor: '#ff0000',
                    verticalDistColor: '#00ff00',
                    initPosAlignmentColor: '#0000ff',
                    lineDash: [0, 0],
                    horizontalDistLine: [0, 0],
                    verticalDistLine: [0, 0],
                    initPosAlignmentLine: [0, 0],
                },
            });
            var edges = workflow.branches.map(function (branch) {
                var edge = { group: 'edges' };
                edge.data = {
                    id: branch.uid,
                    uid: branch.uid,
                    source: branch.source_uid,
                    target: branch.destination_uid,
                };
                return edge;
            });
            var nodes = workflow.actions.map(function (action) {
                var node = { group: 'nodes', position: _.clone(action.position) };
                node.data = {
                    id: action.uid,
                    uid: action.uid,
                    label: action.name,
                    isStartNode: action.uid === workflow.start,
                };
                self._setNodeDisplayProperties(node, action);
                return node;
            });
            _this.cy.add(nodes.concat(edges));
            _this.cy.fit(null, 50);
            _this.setStartNode(workflow.start);
            _this.cy.on('select', 'node', function (e) { return _this.onNodeSelect(e, _this); });
            _this.cy.on('select', 'edge', function (e) { return _this.onEdgeSelect(e, _this); });
            _this.cy.on('unselect', function (e) { return _this.onUnselect(e, _this); });
            _this.cy.on('add', 'node', function (e) { return _this.onNodeAdded(e, _this); });
            _this.cy.on('remove', 'node', function (e) { return _this.onNodeRemoved(e, _this); });
            _this.cy.on('remove', 'edge', function (e) { return _this.onEdgeRemove(e, _this); });
            _this.cyJsonData = JSON.stringify(workflow, null, 2);
            _this._closeWorkflowsModal();
        })
            .catch(function (e) { return _this.toastyService.error("Error loading workflow " + playbookName + " - " + workflowName + ": " + e.message); });
    };
    PlaybookComponent.prototype.closeWorkflow = function () {
        this.currentPlaybook = '';
        this.currentWorkflow = '';
        this.loadedWorkflow = null;
        this.selectedBranchParams = null;
        this.selectedAction = null;
    };
    PlaybookComponent.prototype.save = function () {
        this.saveWorkflow(this.cy.elements().jsons());
    };
    PlaybookComponent.prototype.saveWorkflow = function (cyData) {
        var _this = this;
        var workflowToSave = _.cloneDeep(this.loadedWorkflow);
        if (!workflowToSave.start) {
            this.toastyService.warning('Workflow cannot be saved without a starting action.');
            return;
        }
        workflowToSave.actions.forEach(function (s) {
            s.position = cyData.find(function (cyAction) { return cyAction.data.uid === s.uid; }).position;
            if (s.device_id === 0) {
                delete s.device_id;
            }
            _this._sanitizeArgumentsForSave(s.arguments);
            s.triggers.forEach(function (t) {
                _this._sanitizeArgumentsForSave(t.arguments);
                t.transforms.forEach(function (tr) {
                    _this._sanitizeArgumentsForSave(tr.arguments);
                });
            });
        });
        workflowToSave.branches.forEach(function (ns) {
            ns.conditions.forEach(function (c) {
                _this._sanitizeArgumentsForSave(c.arguments);
                c.transforms.forEach(function (tr) {
                    _this._sanitizeArgumentsForSave(tr.arguments);
                });
            });
        });
        this.playbookService.saveWorkflow(this.currentPlaybook, this.currentWorkflow, workflowToSave)
            .then(function () { return _this.toastyService
            .success("Successfully saved workflow " + _this.currentPlaybook + " - " + _this.currentWorkflow + "."); })
            .catch(function (e) { return _this.toastyService
            .error("Error saving workflow " + _this.currentPlaybook + " - " + _this.currentWorkflow + ": " + e.message); });
    };
    PlaybookComponent.prototype.saveWorkflowJson = function (workflowJSONString) {
    };
    PlaybookComponent.prototype.getPlaybooksWithWorkflows = function () {
        var _this = this;
        this.playbookService.getPlaybooks()
            .then(function (playbooks) { return _this.playbooks = playbooks; });
    };
    PlaybookComponent.prototype._sanitizeArgumentsForSave = function (args) {
        var idsToRemove = [];
        for (var _i = 0, args_1 = args; _i < args_1.length; _i++) {
            var argument = args_1[_i];
            if (typeof (argument.value) === 'string') {
                argument.value = argument.value.trim();
            }
            if ((argument.value == null || argument.value === '') && argument.reference === '') {
                idsToRemove.unshift(args.indexOf(argument));
            }
            if (argument.reference && argument.value) {
                delete argument.value;
            }
        }
        for (var _a = 0, idsToRemove_1 = idsToRemove; _a < idsToRemove_1.length; _a++) {
            var id = idsToRemove_1[_a];
            args.splice(id, 1);
        }
        args.forEach(function (argument) {
            if (argument.selection == null) {
                argument.selection = [];
            }
            else if (typeof (argument.selection) === 'string') {
                argument.selection = argument.selection.trim();
                argument.selection = argument.selection.split('.');
                if (argument.selection[0] === '') {
                    argument.selection = [];
                }
                else {
                    for (var i = 0; i < argument.selection.length; i++) {
                        if (!isNaN(argument.selection[i])) {
                            argument.selection[i] = +argument.selection[i];
                        }
                    }
                }
            }
        });
    };
    PlaybookComponent.prototype.onNodeSelect = function (e, self) {
        var _this = this;
        self.selectedBranchParams = null;
        var data = e.target.data();
        self.cy.elements("[uid!=\"" + data.uid + "\"]").unselect();
        var action = self.loadedWorkflow.actions.find(function (s) { return s.uid === data.uid; });
        if (!action) {
            return;
        }
        var actionApi = this._getAction(action.app_name, action.action_name);
        var queryPromises = [];
        if (!this.users &&
            (actionApi.parameters.findIndex(function (p) { return p.schema.type === 'user'; }) > -1 ||
                actionApi.parameters.findIndex(function (p) { return p.schema.items && p.schema.items.type === 'user'; }) > -1)) {
            this.waitingOnData = true;
            queryPromises.push(this.playbookService.getUsers().then(function (users) { return _this.users = users; }));
        }
        if (!this.roles &&
            (actionApi.parameters.findIndex(function (p) { return p.schema.type === 'role'; }) > -1 ||
                actionApi.parameters.findIndex(function (p) { return p.schema.items && p.schema.items.type === 'role'; }) > -1)) {
            queryPromises.push(this.playbookService.getRoles().then(function (roles) { return _this.roles = roles; }));
        }
        if (queryPromises.length) {
            Promise.all(queryPromises)
                .then(function () {
                _this.waitingOnData = false;
            })
                .catch(function (error) {
                _this.waitingOnData = false;
                _this.toastyService.error("Error grabbing users or roles: " + error.message);
            });
        }
        self.selectedAction = action;
        self.selectedActionApi = actionApi;
        if (!self.selectedAction.triggers) {
            self.selectedAction.triggers = [];
        }
        self.relevantDevices = self.devices.filter(function (d) { return d.app_name === self.selectedAction.app_name; });
    };
    PlaybookComponent.prototype.onEdgeSelect = function (e, self) {
        self.selectedAction = null;
        self.selectedBranchParams = null;
        var uid = e.target.data('uid');
        self.cy.elements("[uid!=\"" + uid + "\"]").unselect();
        var branch = self.loadedWorkflow.branches.find(function (ns) { return ns.uid === uid; });
        var sourceAction = self.loadedWorkflow.actions.find(function (s) { return s.uid === branch.source_uid; });
        self.selectedBranchParams = {
            branch: branch,
            returnTypes: this._getAction(sourceAction.app_name, sourceAction.action_name).returns,
            appName: sourceAction.app_name,
            actionName: sourceAction.action_name,
        };
    };
    PlaybookComponent.prototype.onUnselect = function (event, self) {
        if (self.selectedAction) {
            this.cy.elements("node[uid=\"" + self.selectedAction.uid + "\"]").data('label', self.selectedAction.name);
        }
        if (!self.cy.$(':selected').length) {
            self.selectedAction = null;
            self.selectedBranchParams = null;
        }
    };
    PlaybookComponent.prototype.onEdgeRemove = function (event, self) {
        var edgeData = event.target.data();
        if (!edgeData || edgeData.temp) {
            return;
        }
        var sourceUid = edgeData.source;
        var destinationUid = edgeData.target;
        this.loadedWorkflow.branches = this.loadedWorkflow.branches
            .filter(function (ns) { return !(ns.source_uid === sourceUid && ns.destination_uid === destinationUid); });
    };
    PlaybookComponent.prototype.onNodeAdded = function (event, self) {
        var node = event.target;
        if (node.isNode() && self.cy.nodes().size() === 1) {
            self.setStartNode(node.data('uid'));
        }
    };
    PlaybookComponent.prototype.onNodeRemoved = function (event, self) {
        var node = event.target;
        var data = node.data();
        if (data && node.isNode() && self.loadedWorkflow.start === data.uid) {
            self.setStartNode(null);
        }
        if (self.selectedAction && self.selectedAction.uid === data.uid) {
            self.selectedAction = null;
        }
        this.loadedWorkflow.actions = this.loadedWorkflow.actions.filter(function (s) { return s.uid !== data.uid; });
        this.loadedWorkflow.branches = this.loadedWorkflow.branches
            .filter(function (ns) { return !(ns.source_uid === data.uid || ns.destination_uid === data.uid); });
    };
    PlaybookComponent.prototype.handleDropEvent = function (e) {
        if (this.cy === null) {
            return;
        }
        var appName = e.dragData.appName;
        var actionApi = e.dragData.actionApi;
        var dropPosition = {
            x: e.mouseEvent.layerX,
            y: e.mouseEvent.layerY,
        };
        this.insertNode(appName, actionApi.name, dropPosition, true);
    };
    PlaybookComponent.prototype.handleDoubleClickEvent = function (appName, actionName) {
        if (this.cy === null) {
            return;
        }
        var extent = this.cy.extent();
        function avg(a, b) { return (a + b) / 2; }
        var centerGraphPosition = { x: avg(extent.x1, extent.x2), y: avg(extent.y1, extent.y2) };
        this.insertNode(appName, actionName, centerGraphPosition, false);
    };
    PlaybookComponent.prototype.insertNode = function (appName, actionName, location, shouldUseRenderedPosition) {
        var _this = this;
        var uid = angular2_uuid_1.UUID.UUID();
        var args = [];
        var parameters = this._getAction(appName, actionName).parameters;
        if (parameters && parameters.length) {
            this._getAction(appName, actionName).parameters.forEach(function (parameter) {
                args.push(_this.getDefaultArgument(parameter));
            });
        }
        var actionToBeAdded;
        var numExistingActions = 0;
        this.loadedWorkflow.actions.forEach(function (s) { return s.action_name === actionName ? numExistingActions++ : null; });
        var uniqueActionName = numExistingActions ? actionName + " " + (numExistingActions + 1) : actionName;
        if (appName && actionName) {
            actionToBeAdded = new action_1.Action();
        }
        actionToBeAdded.uid = uid;
        actionToBeAdded.name = uniqueActionName;
        actionToBeAdded.app_name = appName;
        actionToBeAdded.action_name = actionName;
        actionToBeAdded.arguments = args;
        this.loadedWorkflow.actions.push(actionToBeAdded);
        var nodeToBeAdded = {
            group: 'nodes',
            data: {
                id: uid,
                uid: uid,
                label: uniqueActionName,
            },
            renderedPosition: null,
            position: null,
        };
        this._setNodeDisplayProperties(nodeToBeAdded, actionToBeAdded);
        if (shouldUseRenderedPosition) {
            nodeToBeAdded.renderedPosition = location;
        }
        else {
            nodeToBeAdded.position = location;
        }
        this.ur.do('add', nodeToBeAdded);
    };
    PlaybookComponent.prototype.copy = function () {
        this.cy.clipboard().copy(this.cy.$(':selected'));
    };
    PlaybookComponent.prototype.paste = function () {
        var _this = this;
        var newNodes = this.ur.do('paste');
        newNodes.forEach(function (n) {
            var pastedAction = _.clone(_this.loadedWorkflow.actions.find(function (s) { return s.uid === n.data('uid'); }));
            var uid = n.data('id');
            pastedAction.uid = uid;
            n.data({
                uid: uid,
                isStartNode: false,
            });
            _this.loadedWorkflow.actions.push(pastedAction);
        });
    };
    PlaybookComponent.prototype._setNodeDisplayProperties = function (actionNode, action) {
        if (this._getAction(action.app_name, action.action_name).event) {
            actionNode.type = 'eventAction';
        }
        else {
            actionNode.type = 'action';
        }
    };
    PlaybookComponent.prototype.clearExecutionHighlighting = function () {
        this.cy.elements().removeClass('good-highlighted bad-highlighted');
    };
    PlaybookComponent.prototype.setStartNode = function (start) {
        if (start) {
            this.loadedWorkflow.start = start;
        }
        else {
            var roots = this.cy.nodes().roots();
            if (roots.size() > 0) {
                this.loadedWorkflow.start = roots[0].data('uid');
            }
        }
        this.cy.elements('node[?isStartNode]').data('isStartNode', false);
        this.cy.elements("node[uid=\"" + start + "\"]").data('isStartNode', true);
    };
    PlaybookComponent.prototype.removeSelectedNodes = function () {
        var selecteds = this.cy.$(':selected');
        this.cy.elements(':selected').unselect();
        if (selecteds.length > 0) {
            this.ur.do('remove', selecteds);
        }
    };
    PlaybookComponent.prototype._addCytoscapeEventBindings = function () {
        var self = this;
        document.addEventListener('keydown', function (e) {
            var tagName = document.activeElement.tagName;
            if (!(tagName === 'BODY' || tagName === 'BUTTON')) {
                return;
            }
            if (self.cy === null) {
                return;
            }
            if (e.which === 46) {
                self.removeSelectedNodes();
            }
            else if (e.ctrlKey) {
                if (e.which === 67) {
                    self.copy();
                }
                else if (e.which === 86) {
                    self.paste();
                }
            }
        });
    };
    PlaybookComponent.prototype.renamePlaybookModal = function (playbook) {
        var _this = this;
        this._closeWorkflowsModal();
        this.modalParams = {
            title: 'Rename Existing Playbook',
            submitText: 'Rename Playbook',
            shouldShowPlaybook: true,
            submit: function () {
                _this.playbookService.renamePlaybook(playbook, _this.modalParams.newPlaybook)
                    .then(function () {
                    _this.playbooks.find(function (pb) { return pb.name === playbook; }).name = _this.modalParams.newPlaybook;
                    _this.toastyService.success("Successfully renamed playbook \"" + _this.modalParams.newPlaybook + "\".");
                    _this._closeModal();
                })
                    .catch(function (e) { return _this.toastyService.error("Error renaming playbook \"" + _this.modalParams.newPlaybook + "\": " + e.message); });
            },
        };
        this._openModal();
    };
    PlaybookComponent.prototype.duplicatePlaybookModal = function (playbook) {
        var _this = this;
        this._closeWorkflowsModal();
        this.modalParams = {
            title: 'Duplicate Existing Playbook',
            submitText: 'Duplicate Playbook',
            shouldShowPlaybook: true,
            submit: function () {
                _this.playbookService.duplicatePlaybook(playbook, _this.modalParams.newPlaybook)
                    .then(function () {
                    var duplicatedPb = _.cloneDeep(_this.playbooks.find(function (pb) { return pb.name === playbook; }));
                    duplicatedPb.name = _this.modalParams.newPlaybook;
                    _this.playbooks.push(duplicatedPb);
                    _this.playbooks.sort(function (a, b) { return a.name > b.name ? 1 : -1; });
                    _this.toastyService
                        .success("Successfully duplicated playbook \"" + playbook + "\" as \"" + _this.modalParams.newPlaybook + "\".");
                    _this._closeModal();
                })
                    .catch(function (e) { return _this.toastyService
                    .error("Error duplicating playbook \"" + _this.modalParams.newPlaybook + "\": " + e.message); });
            },
        };
        this._openModal();
    };
    PlaybookComponent.prototype.deletePlaybook = function (playbook) {
        var _this = this;
        if (!confirm("Are you sure you want to delete playbook \"" + playbook + "\"?")) {
            return;
        }
        this.playbookService
            .deletePlaybook(playbook)
            .then(function () {
            _this.playbooks = _this.playbooks.filter(function (p) { return p.name !== playbook; });
            if (playbook === _this.currentPlaybook) {
                _this.closeWorkflow();
            }
            _this.toastyService.success("Successfully deleted playbook \"" + playbook + "\".");
        })
            .catch(function (e) { return _this.toastyService
            .error("Error deleting playbook \"" + playbook + "\": " + e.message); });
    };
    PlaybookComponent.prototype.newWorkflowModal = function () {
        var _this = this;
        this._closeWorkflowsModal();
        this.modalParams = {
            title: 'Create New Workflow',
            submitText: 'Add Workflow',
            shouldShowExistingPlaybooks: true,
            shouldShowPlaybook: true,
            shouldShowWorkflow: true,
            submit: function () {
                var playbookName = _this._getModalPlaybookName();
                _this.playbookService.newWorkflow(playbookName, _this.modalParams.newWorkflow)
                    .then(function (newWorkflow) {
                    var pb = _this.playbooks.find(function (p) { return p.name === playbookName; });
                    if (pb) {
                        pb.workflows.push(newWorkflow);
                        pb.workflows.sort(function (a, b) { return a.name > b.name ? 1 : -1; });
                    }
                    else {
                        _this.playbooks.push({ name: playbookName, workflows: [newWorkflow], uid: null });
                        _this.playbooks.sort(function (a, b) { return a.name > b.name ? 1 : -1; });
                    }
                    if (!_this.loadedWorkflow) {
                        _this.loadWorkflow(playbookName, _this.modalParams.newWorkflow);
                    }
                    _this.toastyService.success("Created workflow \"" + playbookName + " - " + _this.modalParams.newWorkflow + "\".");
                    _this._closeModal();
                })
                    .catch(function (e) { return _this.toastyService
                    .error("Error creating workflow \"" + playbookName + " - " + _this.modalParams.newWorkflow + "\": " + e.message); });
            },
        };
        this._openModal();
    };
    PlaybookComponent.prototype.renameWorkflowModal = function (playbook, workflow) {
        var _this = this;
        this._closeWorkflowsModal();
        this.modalParams = {
            title: 'Rename Existing Workflow',
            submitText: 'Rename Workflow',
            shouldShowWorkflow: true,
            submit: function () {
                var playbookName = _this._getModalPlaybookName();
                _this.playbookService.renameWorkflow(playbook, workflow, _this.modalParams.newWorkflow)
                    .then(function () {
                    _this.playbooks
                        .find(function (pb) { return pb.name === playbook; }).workflows
                        .find(function (wf) { return wf.name === workflow; }).name = _this.modalParams.newWorkflow;
                    if (_this.currentPlaybook === playbook && _this.currentWorkflow === workflow && _this.loadedWorkflow) {
                        _this.loadedWorkflow.name = _this.modalParams.newWorkflow;
                        _this.currentWorkflow = _this.modalParams.newWorkflow;
                    }
                    _this.toastyService.success("Successfully renamed workflow \"" + playbookName + " - " + _this.modalParams.newWorkflow + "\".");
                    _this._closeModal();
                })
                    .catch(function (e) { return _this.toastyService
                    .error("Error renaming workflow \"" + playbookName + " - " + _this.modalParams.newWorkflow + "\": " + e.message); });
            },
        };
        this._openModal();
    };
    PlaybookComponent.prototype.duplicateWorkflowModal = function (playbook, workflow) {
        var _this = this;
        this._closeWorkflowsModal();
        this.modalParams = {
            title: 'Duplicate Existing Workflow',
            submitText: 'Duplicate Workflow',
            selectedPlaybook: playbook,
            shouldShowWorkflow: true,
            submit: function () {
                var playbookName = _this._getModalPlaybookName();
                _this.playbookService.duplicateWorkflow(playbook, workflow, _this.modalParams.newWorkflow)
                    .then(function (duplicatedWorkflow) {
                    var pb = _this.playbooks.find(function (p) { return p.name === playbook; });
                    if (!pb) {
                        pb = { uid: null, name: _this._getModalPlaybookName(), workflows: [] };
                        _this.playbooks.push(pb);
                        _this.playbooks.sort(function (a, b) { return a.name > b.name ? 1 : -1; });
                    }
                    pb.workflows.push(duplicatedWorkflow);
                    pb.workflows.sort(function (a, b) { return a.name > b.name ? 1 : -1; });
                    _this.toastyService
                        .success("Successfully duplicated workflow \"" + playbookName + " - " + _this.modalParams.newWorkflow + "\".");
                    _this._closeModal();
                })
                    .catch(function (e) { return _this.toastyService
                    .error("Error duplicating workflow \"" + playbookName + " - " + _this.modalParams.newWorkflow + "\": " + e.message); });
            },
        };
        this._openModal();
    };
    PlaybookComponent.prototype.deleteWorkflow = function (playbook, workflow) {
        var _this = this;
        if (!confirm("Are you sure you want to delete workflow \"" + playbook + " - " + workflow + "\"?")) {
            return;
        }
        this.playbookService
            .deleteWorkflow(playbook, workflow)
            .then(function () {
            var pb = _this.playbooks.find(function (p) { return p.name === playbook; });
            pb.workflows = pb.workflows.filter(function (w) { return w.name !== workflow; });
            if (!pb.workflows.length) {
                _this.playbooks = _this.playbooks.filter(function (p) { return p.name !== pb.name; });
            }
            if (playbook === _this.currentPlaybook && workflow === _this.currentWorkflow) {
                _this.closeWorkflow();
            }
            _this.toastyService.success("Successfully deleted workflow \"" + playbook + " - " + workflow + "\".");
        })
            .catch(function (e) { return _this.toastyService.error("Error deleting workflow \"" + playbook + " - " + workflow + "\": " + e.message); });
    };
    PlaybookComponent.prototype._openModal = function () {
        $('#playbookAndWorkflowActionModal').modal('show');
    };
    PlaybookComponent.prototype._closeModal = function () {
        $('#playbookAndWorkflowActionModal').modal('hide');
    };
    PlaybookComponent.prototype._closeWorkflowsModal = function () {
        $('#workflowsModal').modal('hide');
    };
    PlaybookComponent.prototype._getModalPlaybookName = function () {
        if (this.modalParams.selectedPlaybook && this.modalParams.selectedPlaybook !== '') {
            return this.modalParams.selectedPlaybook;
        }
        return this.modalParams.newPlaybook;
    };
    PlaybookComponent.prototype.getPlaybooks = function () {
        return this.playbooks.map(function (pb) { return pb.name; });
    };
    PlaybookComponent.prototype._doesWorkflowExist = function (playbook, workflow) {
        var matchingPB = this.playbooks.find(function (pb) { return pb.name === playbook; });
        if (!matchingPB) {
            return false;
        }
        return matchingPB.workflows.findIndex(function (wf) { return wf.name === workflow; }) >= 0;
    };
    PlaybookComponent.prototype.getPreviousActions = function () {
        return this.loadedWorkflow.actions;
    };
    PlaybookComponent.prototype._getAction = function (appName, actionName) {
        return this.appApis.find(function (a) { return a.name === appName; }).action_apis.find(function (a) { return a.name === actionName; });
    };
    PlaybookComponent.prototype.getOrInitializeSelectedActionArgument = function (parameterApi) {
        var argument = this.selectedAction.arguments.find(function (a) { return a.name === parameterApi.name; });
        if (argument) {
            return argument;
        }
        argument = this.getDefaultArgument(parameterApi);
        this.selectedAction.arguments.push(argument);
        return argument;
    };
    PlaybookComponent.prototype.getDefaultArgument = function (parameterApi) {
        return {
            name: parameterApi.name,
            value: parameterApi.schema.default != null ? parameterApi.schema.default : null,
            reference: '',
            selection: '',
        };
    };
    PlaybookComponent.prototype.getConditionApis = function (appName) {
        return this.appApis.find(function (a) { return a.name === appName; }).condition_apis;
    };
    PlaybookComponent.prototype.getTransformApis = function (appName) {
        return this.appApis.find(function (a) { return a.name === appName; }).transform_apis;
    };
    PlaybookComponent.prototype.getDeviceApis = function (appName) {
        return this.appApis.find(function (a) { return a.name === appName; }).device_apis;
    };
    PlaybookComponent.prototype.getInputApiArgs = function (appName, actionName, inputName) {
        return this._getAction(appName, actionName).parameters.find(function (a) { return a.name === inputName; });
    };
    PlaybookComponent.prototype.getAppsWithActions = function () {
        return this.appApis.filter(function (a) { return a.action_apis && a.action_apis.length; });
    };
    PlaybookComponent.prototype.getFriendlyJSON = function (input) {
        var out = JSON.stringify(input, null, 1);
        out = out.replace(/[\{\[\}\]"]/g, '').trim();
        if (!out) {
            return 'N/A';
        }
        return out;
    };
    PlaybookComponent.prototype.getFriendlyArguments = function (args) {
        if (!args || !args.length) {
            return 'N/A';
        }
        var obj = {};
        args.forEach(function (element) {
            if (element.value) {
                obj[element.name] = element.value;
            }
            if (element.reference) {
                obj[element.name] = element.reference;
            }
            if (element.selection) {
                var selectionString = element.selection.join('.');
                obj[element.name] = obj[element.name] + " (" + selectionString + ")";
            }
        });
        var out = JSON.stringify(obj, null, 1);
        out = out.replace(/[\{\}"]/g, '');
        return out;
    };
    return PlaybookComponent;
}());
__decorate([
    core_1.ViewChild('cyRef'),
    __metadata("design:type", core_1.ElementRef)
], PlaybookComponent.prototype, "cyRef", void 0);
__decorate([
    core_1.ViewChild('workflowResultsContainer'),
    __metadata("design:type", core_1.ElementRef)
], PlaybookComponent.prototype, "workflowResultsContainer", void 0);
__decorate([
    core_1.ViewChild('workflowResultsTable'),
    __metadata("design:type", ngx_datatable_1.DatatableComponent)
], PlaybookComponent.prototype, "workflowResultsTable", void 0);
PlaybookComponent = __decorate([
    core_1.Component({
        selector: 'playbook-component',
        templateUrl: 'client/playbook/playbook.html',
        styleUrls: [
            'client/playbook/playbook.css',
        ],
        encapsulation: core_1.ViewEncapsulation.None,
        providers: [playbook_service_1.PlaybookService, auth_service_1.AuthService],
    }),
    __metadata("design:paramtypes", [playbook_service_1.PlaybookService, auth_service_1.AuthService,
        ng2_toasty_1.ToastyService, ng2_toasty_1.ToastyConfig,
        core_1.ChangeDetectorRef])
], PlaybookComponent);
exports.PlaybookComponent = PlaybookComponent;
