import { Component, ViewEncapsulation, ViewChild, ElementRef } from '@angular/core';
// import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';
// import * as cytoscape from 'cytoscape';
// import * as cytoscapeClipboard from 'cytoscape-clipboard';
// import * as cytoscapeEdgehandles from 'cytoscape-edgehandles';
// import * as cytoscapeGridGuide from 'cytoscape-grid-guide';
// import * as cytoscapePanzoom from 'cytoscape-panzoom';
// import * as cytoscapeUndoRedo from 'cytoscape-undo-redo';
// import * as jstree from 'jstree';
import { UUID } from 'angular2-uuid';
// import { TreeModel, Ng2TreeSettings, TreeModelSettings } from 'ng2-tree';
// import { TreeComponent, TreeModel, TreeNode } from 'angular-tree-component';

import { PlaybookService } from './playbook.service';
import { AuthService } from '../auth/auth.service';

import { Action, ActionArgument } from '../models/playbook/action';
import { Playbook } from '../models/playbook/playbook';
import { Workflow } from '../models/playbook/workflow';
import { Condition } from '../models/playbook/condition';
import { Transform } from '../models/playbook/transform';
import { GraphPosition } from '../models/playbook/graphPosition';
import { Device } from '../models/device';

// declare function cytoscape(options: any): any;

@Component({
	selector: 'playbook-component',
	templateUrl: 'client/playbook/playbook.html',
	styleUrls: [
		'client/playbook/playbook.css'
	],
	encapsulation: ViewEncapsulation.None,
	providers: [PlaybookService, AuthService]
})
export class PlaybookComponent {
	@ViewChild('cyRef') cyRef: ElementRef;

	conditions: Condition[] = [];
	transforms: Transform[] = [];
	devices: Device[] = [];

	currentPlaybook: string;
	currentWorkflow: string;
	loadedWorkflow: Workflow;
	workflowsForPlaybooks: Playbook[] = [];
	cy: any;
	ur: any;
	actionsForApps: { [key: string]: { [key: string]: Action } } = {};
	startNode: string;
	offset: GraphPosition = { x: -330, y: -170 };
	selectedNode: any = null; // node being displayed in json editor
	cyJsonData: string;
	actionTree: any;

	// Simple bootstrap modal params
	modalParams: {
		title: string,
		submitText: string,
		shouldShowPlaybook?: boolean,
		shouldShowExistingPlaybooks?: boolean,
		selectedPlaybook?: string,
		newPlaybook?: string,
		shouldShowWorkflow?: boolean,
		newWorkflow?: string,
		submit?: () => any
	} = {
		title: '',
		submitText: '',
		shouldShowPlaybook: false,
		shouldShowExistingPlaybooks: false,
		selectedPlaybook: '',
		newPlaybook: '',
		shouldShowWorkflow: false,
		newWorkflow: '',
		submit: <() => any>(() => {})
	};

	constructor(private playbookService: PlaybookService, private authService: AuthService, private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';

		this.playbookService.getConditions().then(conditions => this.conditions = conditions);
		this.playbookService.getTransforms().then(transforms => this.transforms = transforms);
		this.playbookService.getDevices().then(devices => this.devices = devices);
		this.getActionsForApps();
		this.getWorkflowResultsSSE();
		this.getPlaybooksWithWorkflows();

		// Register cytoscape plugins
		// cytoscapeClipboard(cytoscape, $); // jquery
		// cytoscapeEdgehandles(cytoscape, _.debounce, _.throttle);
		// cytoscapeGridGuide(cytoscape, $); // jquery
		// cytoscapePanzoom(cytoscape, $);
		// cytoscapeUndoRedo(cytoscape);

		this._addCytoscapeEventBindings();
	}

	///------------------------------------------------------------------------------------------------------
	/// Playbook CRUD etc functions
	///------------------------------------------------------------------------------------------------------
	getWorkflowResultsSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const observable = Observable.create((observer: any) => {
					const eventSource = new (<any>window)['EventSource']('workflowresults/stream-steps?access_token=' + authToken);
					eventSource.onmessage = (x: Object) => observer.next(x);
					eventSource.onerror = (x: Error) => observer.error(x);

					return () => {
						eventSource.close();
					};
				});

				observable.subscribe({
					next: (workflowResult: Object) => {
						// add to a table
					},
					error: (err: Error) => {

						// This function removes selected nodes and edges
						this.toastyService.error(`Error retrieving workflow results: ${err.message}`);
						console.error(err);
					}
				});
			});
	}

	executeWorkflow(): void {
		this.playbookService.executeWorkflow(this.currentPlaybook, this.currentWorkflow)
			.then(() => this.toastyService.success(`Starting execution of ${this.currentPlaybook} - ${this.currentWorkflow}.`))
			.catch(e => this.toastyService.error(`Error starting execution of ${this.currentPlaybook} - ${this.currentWorkflow}: ${e.message}`));
	}

	loadWorkflow(playbookName: string, workflowName: string): void {
		let self = this;

		this.playbookService.loadWorkflow(playbookName, workflowName)
			.then(workflow => {
				this.currentPlaybook = playbookName;
				this.currentWorkflow = workflowName;
				this.loadedWorkflow = workflow;

				// Create the Cytoscape graph
				this.cy = cytoscape({
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
								'height': '40'
							}
						},
						{
							selector: 'node[type="action"]',
							css: {
								'background-color': '#bbb',
							}
						},
						{
							selector: 'node[type="eventAction"]',
							css: {
								'shape': 'star',
								'background-color': '#edbd21',
							}
						},
						{
							selector: 'node:selected',
							css: {
								'background-color': '#45F'
							}
						},
						{
							selector: '.good-highlighted',
							css: {
								'background-color': '#399645',
								'transition-property': 'background-color',
								'transition-duration': '0.5s'
							}
						},
						{
							selector: '.bad-highlighted',
							css: {
								'background-color': '#8e3530',
								'transition-property': 'background-color',
								'transition-duration': '0.5s'
							}
						},
						{
							selector: '$node > node',
							css: {
								'padding-top': '10px',
								'padding-left': '10px',
								'padding-bottom': '10px',
								'padding-right': '10px',
								'text-valign': 'top',
								'text-halign': 'center'
							}
						},
						{
							selector: 'edge',
							css: {
								'target-arrow-shape': 'triangle',
								'curve-style': 'bezier',
							}
						}
					]
				});

				// Enable various Cytoscape extensions
				// Undo/Redo extension
				this.ur = this.cy.undoRedo({});

				// Panzoom extension
				this.cy.panzoom({});

				// Extension for drawing edges
				this.cy.edgehandles({
					preview: false,
					toggleOffOnLeave: true,
					complete: function (sourceNode: any, targetNodes: any[], addedEntities: any[]) {
						let sourceParameters = sourceNode.data().parameters;
						if (!sourceParameters.hasOwnProperty("next"))
							sourceParameters.next = [];

						// The edge handles extension is not integrated into the undo/redo extension.
						// So in order that adding edges is contained in the undo stack,
						// remove the edge just added and add back in again using the undo/redo
						// extension. Also add info to edge which is displayed when user clicks on it.
						for (let i = 0; i < targetNodes.length; i++) {
							addedEntities[i].data('parameters', {
								flags: [],
								name: targetNodes[i].data().parameters.name,
								nextStep: targetNodes[i].data().parameters.name,
								temp: true
							});

							//If we attempt to draw an edge that already exists, please remove it and take no further action
							if (sourceParameters.next.find((next: any) => { return next.name === targetNodes[i].data().id })) {
								self.cy.remove(addedEntities);
								return;
							}

							sourceParameters.next.push({
								flags: [],
								status: 'Success',
								name: targetNodes[i].data().id // Note use id, not name since name can be changed
							});

							sourceNode.data('parameters', sourceParameters);
						}

						self.cy.remove(addedEntities);

						addedEntities.forEach((ae: any) => {
							let data = ae.data();
							delete data.parameters.temp;
							ae.data(data);
						});

						let newEdges = self.ur.do('add', addedEntities); // Added back in using undo/redo extension
					},
				});

				// Extension for copy and paste
				this.cy.clipboard();

				//Extension for grid and guidelines
				this.cy.gridGuide();

				// Load the data into the graph
				// If a node does not have a label field, set it to
				// the action. The label is what is displayed in the graph.
				let edges: any[] = [];
				let steps = workflow.steps.map(function (value) {
					var ret: any = { group: "nodes", position: _.clone(value.position) };
					ret.data = { id: value.uid, parameters: _.cloneDeep(value), label: value.name, isStartNode: value.uid === workflow.start };
					self._setNodeDisplayProperties(ret);
					value.next.forEach((nextStep) => {
						edges.push({
							group: "edges",
							data: {
								id: nextStep.uid,
								source: value.uid,
								target: nextStep.uid,
								parameters: _.clone(nextStep)
							}
						});
					});
					return ret;
				});

				steps = steps.concat(edges);
				this.cy.add(steps);

				this.cy.fit(null, 50);

				this.setStartNode(workflow.start);

				// Configure handler when user clicks on node or edge
				this.cy.on('select', 'node', (e: any) => this.onNodeSelect(e, this));
				this.cy.on('select', 'edge', (e: any) => this.onEdgeSelect(e, this));
				this.cy.on('unselect', (e: any) => this.onUnselect(e, this));

				// Configure handlers when nodes/edges are added or removed
				this.cy.on('add', 'node', (e: any) => this.onNodeAdded(e, this));
				this.cy.on('remove', 'node', (e: any) => this.onNodeRemoved(e, this));
				this.cy.on('remove', 'edge', (e: any) => this.onEdgeRemove(e, this));

				this.cyJsonData = JSON.stringify(workflow, null, 2);
			})
			.catch(e => this.toastyService.error(`Error loading workflow ${playbookName} - ${workflowName}: ${e.message}`));
	}

	save(): void {
		if ($(".nav-tabs .active").text() === "Graphical Editor") {
			// If the graphical editor tab is active
			this.saveWorkflow(this.cy.elements().jsons());
		}
		else {
			// If the JSON tab is active
			this.saveWorkflowJson(this.cyJsonData);
		}
	}

	saveWorkflow(workflowData: any): void {
		if (!this.startNode) {
			this.toastyService.warning(`Workflow cannot be saved without a starting step.`);
			return;
		}

		workflowData = _.filter(workflowData, function (data: any) { return data.group === "nodes"; });

		let steps = _.map(workflowData, function (step: any) {
			let ret = _.cloneDeep(step.data.parameters);
			ret.position = _.clone(step.position);
			return ret;
		});

		// this._transformInputsToSave(steps);

		this.playbookService.saveWorkflow(this.currentPlaybook, this.currentWorkflow, { start: this.startNode, steps: steps })
			.then(() => this.toastyService.success(`Successfully saved workflow ${this.currentPlaybook} - ${this.currentWorkflow}.`))
			.catch(e => this.toastyService.error(`Error saving workflow ${this.currentPlaybook} - ${this.currentWorkflow}: ${e.message}`));
	}


	saveWorkflowJson(workflowJSONString: string): void {
		// // Convert data in string format under JSON tab to a dictionary
		// let dataJson = JSON.parse(workflowJSONString);

		// // Get current list of steps from cytoscape data in JSON format
		// let workflowData = this.cy.elements().jsons();

		// // Track existing steps using a dictionary where the keys are the
		// // step ID and the values are the index of the step in workflowData
		// let ids: { [key: string]: string } = {};
		// for (let step = 0; step < workflowData.length; step++) {
		// 	ids[workflowData[step].data.id] = step.toString();
		// }

		// // Compare current list of steps with updated list and modify current list
		// let stepsJson = dataJson.steps; // Get updated list of steps
		// stepsJson.forEach(function (stepJson: any) {
		// 	let idJson = stepJson.data.id;
		// 	if (idJson in ids) {
		// 		// If step already exists, then just update its fields
		// 		let step = Number(ids[idJson])
		// 		workflowData[step].data = stepJson.data;
		// 		workflowData[step].group = stepJson.group;
		// 		workflowData[step].position = stepJson.position;
		// 		// Delete step id
		// 		delete ids[idJson]
		// 	} else {
		// 		// If step is absent, then create a new step
		// 		let newStep = getStepTemplate();
		// 		newStep.data = stepJson.data;
		// 		newStep.group = stepJson.group;
		// 		newStep.position = stepJson.position;
		// 		// Add new step
		// 		workflowData.push(newStep)
		// 	}
		// })

		// if (Object.keys(ids).length > 0) {
		// 	// If steps have been removed, then delete steps
		// 	for (let id in Object.keys(ids)) {
		// 		let step = Number(ids[idJson])
		// 		workflowData.splice(step, 1)
		// 	}
		// }

		// // Save updated cytoscape data in JSON format
		// this.saveWorkflow(workflowData);
	}

	getPlaybooksWithWorkflows(): void {
		this.playbookService.getPlaybooks()
			.then(playbooks => this.workflowsForPlaybooks = playbooks);
	}

	getActionsForApps(): void {
		this.playbookService.getActionsForApps()
			.then((actionsForApps) => {
				this.actionsForApps = actionsForApps;

				this.actionTree = _.reduce(actionsForApps, function (result: any[], actionObj: { [key: string]: Action }, app: string) {
					let appObj: any = { name: app, children: [] };
					
					Object.keys(actionObj).forEach(actionName => appObj.children.push({ name: actionName, id: app }));

					result.push(appObj);

					return result;
				}, []);

				console.log(this.actionTree);
			});
	}

	///------------------------------------------------------------------------------------------------------
	/// Cytoscape functions
	///------------------------------------------------------------------------------------------------------
	// This function displays a form next to the graph for editing a node when clicked upon
	onNodeSelect(e: any, self: PlaybookComponent): void {
		let ele = e.target;
		let parameters = ele.data('parameters');

		self.selectedNode = ele;

		// ele.data('parameters', updatedParameters);
	}

	onEdgeSelect(event: any, self: PlaybookComponent): void {
		return;
	}

	onUnselect(event: any, self: PlaybookComponent): void {
		if (!self.cy.$('node:selected').length) self.selectedNode = null;
	}

	// when an edge is removed, check the edges that still exist and remove the "next" steps for those that don't
	onEdgeRemove(event: any, self: PlaybookComponent): void {
		let edgeData = event.target.data();
		// Do nothing if this is a temporary edge (edgehandles do not have paramters, and we mark temp edges on edgehandle completion)
		if (!edgeData.parameters || edgeData.parameters.temp) return;

		let parentNode = event.target.source();
		let parentData = _.cloneDeep(parentNode.data());

		parentData.parameters.next = _.reject(parentData.parameters.next, (next: any) => { return next.name === event.target.data().target; });
		parentNode.data(parentData);
	}

	onNodeAdded(event: any, self: PlaybookComponent): void {
		let node = event.target;

		// If the number of nodes in the graph is one, set the start node to it.
		if (node.isNode() && self.cy.nodes().size() === 1) self.setStartNode(node.data("parameters").id);
	}

	onNodeRemoved(event: any, self: PlaybookComponent): void {
		let node = event.target;
		let parameters = node.data("parameters");

		// If the start node was deleted, set it to one of the roots of the graph
		if (parameters && node.isNode() && self.startNode == parameters.id) self.setStartNode(null);
		if (self.selectedNode == node) self.selectedNode = null;
	}

	// This function is called when the user drops a new node onto the graph
	handleDropEvent(event: any, ui: any): void {
		if (this.cy === null) return;

		let draggable = ui.draggable;
		let draggableId = draggable.attr('id');
		// let draggableNode = $('#actions').jstree(true).get_node(draggableId);
		let draggableNode: any = {};
		if (!draggableNode.data)
			return;
		let app = draggableNode.data.app;
		let action = draggableNode.text;

		// The following coordinates is where the user dropped relative to the
		// top-left of the graph
		let location: GraphPosition = {
			x: event.pageX + this.offset.x,
			y: event.pageY + this.offset.y
		}

		this.insertNode(app, action, location, true);
	}

	insertNode(app: string, action: string, location: GraphPosition, shouldUseRenderedPosition: boolean): void {
		// Grab a new UUID for both the ID of the node and the ID of the step in the workflow
		let id = UUID.UUID();

		let inputs: { [key: string]: { name: string, value: string } } = {};
		let actionInfo = this.actionsForApps[app][action];
		actionInfo.args.forEach((input) => {
			// let defaultValue;
			// if (input.type === "string")
			// 	defaultValue = input.default || "";
			// else if (input.type === "boolean")
			// 	defaultValue = input.default || false;
			// else
			// 	defaultValue = input.default || 0;

			inputs[input.name] = {
				name: input.name,
				value: input.default
			};
		});

		// Add the node with the id just found to the graph in the location dropped
		// into by the mouse.
		let nodeToBeAdded = {
			group: 'nodes',
			data: {
				id: id,
				label: action,
				parameters: {
					action: action,
					app: app,
					device_id: 0,
					errors: <any[]>[],
					inputs: inputs,
					uid: id,
					name: action,
					next: <any[]>[],
				}
			},
			renderedPosition: <GraphPosition>null,
			position: <GraphPosition>null,
		};

		this._setNodeDisplayProperties(nodeToBeAdded);

		if (shouldUseRenderedPosition) nodeToBeAdded.renderedPosition = location;
		else nodeToBeAdded.position = location;

		let newNode = this.ur.do('add', nodeToBeAdded);
	}

	cut(): void {
		let selecteds = this.cy.$(":selected");
		if (selecteds.length > 0) {
			this.cy.clipboard().copy(selecteds);
			this.ur.do("remove", selecteds);
		}
	}

	copy(): void {
		this.cy.clipboard().copy(this.cy.$(":selected"));
	}

	paste(): void {
		let newNodes = this.ur.do("paste");

		// Change the names of these new nodes so that they are the
		// same as the id. This is needed since only the name is
		// stored on the server and serves as the unique id of the
		// node. It therefore must be the same as the Cytoscape id.
		// Also delete the next field since user needs to explicitely
		// create new edges for the new node.
		for (let i = 0; i < newNodes.length; ++i) {
			let parameters = newNodes[i].data("parameters");
			parameters.name = newNodes[i].data("id");
			parameters.next = [];
			newNodes[i].data("parameters", parameters);
		}
	}

	_setNodeDisplayProperties(step: any): void {
		//add a type field to handle node styling
		if (this.actionsForApps[step.data.parameters.app][step.data.parameters.action].event) step.data.type = 'eventAction';
		else step.data.type = 'action';
	}

	clearExecutionHighlighting(): void {
		this.cy.elements().removeClass("good-highlighted bad-highlighted");
	}

	setStartNode(start: string): void {
		// If no start was given set it to one of the root nodes
		if (start) {
			this.startNode = start;
		}
		else {
			let roots = this.cy.nodes().roots();
			if (roots.size() > 0) {
				this.startNode = roots[0].data("parameters").id;
			}
		}
	}

	removeSelectedNodes(): void {
		let selecteds = this.cy.$(":selected");
		if (selecteds.length > 0) this.ur.do("remove", selecteds);
	}

	_addCytoscapeEventBindings(): void {
		let self = this;

		// Handle keyboard presses on graph
		document.addEventListener("keydown", function (e) {
			if (self.cy === null) return;

			if (e.which === 46) { // Delete
				self.removeSelectedNodes();
			}

			else if (e.ctrlKey) {
				//TODO: re-enable undo/redo once we restructure how next steps / edges are stored
				// if (e.which === 90) // 'Ctrl+Z', Undo
				//     ur.undo();
				// else if (e.which === 89) // 'Ctrl+Y', Redo
				//     ur.redo();
				if (e.which == 67) // Ctrl + C, Copy
					self.copy();
				else if (e.which == 86) // Ctrl + V, Paste
					self.paste();
				else if (e.which == 88) // Ctrl + X, Cut
					self.cut();
				// else if (e.which == 65) { // 'Ctrl+A', Select All
				//     cy.elements().select();
				//     e.preventDefault();
				// }
			}
		});
	}

	///------------------------------------------------------------------------------------------------------
	/// Simple bootstrap modal stuff
	///------------------------------------------------------------------------------------------------------
	renamePlaybookModal(playbook: string): void {
		this.modalParams = {
			title: 'Rename Existing Playbook',
			submitText: 'Rename Playbook',
			shouldShowPlaybook: true,
			submit: () => {
				this.playbookService.renamePlaybook(playbook, this.modalParams.newPlaybook)
					.then(() => {
						this.workflowsForPlaybooks.find(pb => pb.name === playbook).name = this.modalParams.newPlaybook;
						this.toastyService.success(`Successfully renamed ${this.modalParams.newPlaybook}.`);
						this._closeModal();
					})
					.catch(e => this.toastyService.error(`Error renaming ${this.modalParams.newPlaybook}: ${e.message}`));
			}
		};

		this._openModal();
	}

	duplicatePlaybookModal(playbook: string): void {
		this.modalParams = {
			title: 'Duplicate Existing Playbook',
			submitText: 'Duplicate Playbook',
			shouldShowPlaybook: true,
			submit: () => {
				this.playbookService.duplicatePlaybook(playbook, this.modalParams.newPlaybook)
					.then(() => {
						let duplicatedPb = _.cloneDeep(this.workflowsForPlaybooks.find(pb => pb.name === playbook));
						duplicatedPb.name = this.modalParams.newPlaybook;
						this.toastyService.success(`Successfully duplicated ${playbook} as ${this.modalParams.newPlaybook}.`);
						this._closeModal();
					})
					.catch(e => this.toastyService.error(`Error duplicating ${this.modalParams.newPlaybook}: ${e.message}`));
			}
		};

		this._openModal();
	}

	newWorkflowModal(): void {
		this.modalParams = {
			title: 'Create New Workflow',
			submitText: 'Add Workflow',
			shouldShowExistingPlaybooks: true,
			shouldShowPlaybook: true,
			shouldShowWorkflow: true,
			submit: () => {
				this.playbookService.newWorkflow(this._getModalPlaybookName(), this.modalParams.newWorkflow)
					.then(() => {
						this.toastyService.success(`Created workflow ${this._getModalPlaybookName()} - ${this.modalParams.newWorkflow}.`);
						this._closeModal();
					})
					.catch(e => this.toastyService.error(`Error creating ${this._getModalPlaybookName()} - ${this.modalParams.newWorkflow}: ${e.message}`));
			}
		};

		this._openModal();
	}

	renameWorkflowModal(playbook: string, workflow: string): void {
		this.modalParams = {
			title: 'Rename Existing Workflow',
			submitText: 'Rename Workflow',
			shouldShowWorkflow: true,
			submit: () => {
				this.playbookService.renameWorkflow(playbook, workflow, this.modalParams.newWorkflow)
					.then(() => {
						this.workflowsForPlaybooks.find(pb => pb.name === playbook).workflows.find(wf => wf.name === workflow).name = this.modalParams.newWorkflow;
						this.toastyService.success(`Successfully renamed ${this._getModalPlaybookName()} - ${this.modalParams.newWorkflow}.`);
						this._closeModal();
					})
					.catch(e => this.toastyService.error(`Error renaming ${this._getModalPlaybookName()} - ${this.modalParams.newWorkflow}: ${e.message}`));
			}
		};

		this._openModal();
	}

	duplicateWorkflowModal(playbook: string, workflow: string): void {
		this.modalParams = {
			title: 'Duplicate Existing Workflow',
			submitText: 'Duplicate Workflow',
			shouldShowPlaybook: true,
			shouldShowExistingPlaybooks: true,
			selectedPlaybook: playbook,
			shouldShowWorkflow: true,
			submit: () => {
				this.playbookService.duplicateWorkflow(playbook, workflow, this.modalParams.newWorkflow)
					.then(duplicatedWorkflow => {
						let pb = this.workflowsForPlaybooks.find(pb => pb.name === playbook);

						if (!pb) {
							pb = { uid: null, name: this._getModalPlaybookName(), workflows: [] };
							this.workflowsForPlaybooks.push(pb);
						}

						pb.workflows.push(duplicatedWorkflow);
						this.toastyService.success(`Successfully renamed ${this._getModalPlaybookName()} - ${this.modalParams.newWorkflow}.`);
						this._closeModal();
					})
					.catch(e => this.toastyService.error(`Error renaming ${this._getModalPlaybookName()} - ${this.modalParams.newWorkflow}: ${e.message}`));
			}
		};

		this._openModal();
	}

	_openModal(): void {
		($('#playbookAndWorkflowActionModal') as any).modal('show');
	}

	_closeModal(): void {
		($('#playbookAndWorkflowActionModal') as any).modal('hide');
	}
	
	_getModalPlaybookName(): string {
		if (this.modalParams.selectedPlaybook && this.modalParams.selectedPlaybook !== '0')
			return this.modalParams.selectedPlaybook;

		return this.modalParams.newPlaybook;
	}

	///------------------------------------------------------------------------------------------------------
	/// Utility functions
	///------------------------------------------------------------------------------------------------------
	getPlaybooks(): string[] {
		return this.workflowsForPlaybooks.map(pb => pb.name);
	}

	_doesWorkflowExist(playbook: string, workflow: string): boolean {
		let matchingPB = this.workflowsForPlaybooks.find(pb => pb.name == playbook);

		if (!matchingPB) return false;

		return matchingPB.workflows.findIndex(wf => wf.name === workflow ) >= 0;
	}

	_doesPlaybookExist(playbook: string): boolean {
		return this.workflowsForPlaybooks.hasOwnProperty(playbook);
	}
}
