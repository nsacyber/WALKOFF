import { Component, ViewEncapsulation } from '@angular/core';
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';
import * as cytoscape from 'cytoscape';
import * as cytoscapeClipboard from 'cytoscape-clipboard';
import * as cytoscapeEdgehandles from 'cytoscape-edgehandles';
import * as cytoscapeGridGuide from 'cytoscape-grid-guide';
import * as cytoscapePanzoom from 'cytoscape-panzoom';
import * as cytoscapeUndoRedo from 'cytoscape-undo-redo';
import { UUID } from 'angular2-uuid';

import { PlaybookService } from './playbook.service';
import { AuthService } from '../auth/auth.service';

import { Workflow } from '../models/playbook/workflow';
import { Condition } from '../models/playbook/condition';
import { Transform } from '../models/playbook/transform';
import { Device } from '../models/device';

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
	conditions: Condition[] = [];
	transforms: Transform[] = [];
	devices: Device[] = [];

	currentPlaybook: string;
	currentWorkflow: string;
	loadedWorkflow: Workflow;
	workflowsForPlaybooks: { [key: string] : string[] } = {};
	cy: any;
	ur: any;
	actionsForApps: { [key: string] : { [key: string] : any } } = {};
	startNode: string;
	offsetX: number = -330;
	offsetY: number = -170;
	selectedNode: any = null; // node being displayed in json editor

	// Cytoscape options
	cyOptions = {
		container: document.getElementById('cy'),

		boxSelectionEnabled: false,
		autounselectify: false,
		wheelSensitivity: 0.1,
		layout: { name: 'preset' },
		style: [
			{
				selector: 'node[type="action"]',
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
					'width':'40',
					'height':'40'
				}
			},
			{
				selector: 'node[type="eventAction"]',
				css: {
					'content': 'data(label)',
					'text-valign': 'center',
					'text-halign': 'center',
					'shape': 'star',
					'background-color': '#edbd21',
					'selection-box-color': 'red',
					'font-family': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif, sans-serif',
					'font-weight': 'lighter',
					'font-style': 'italic',
					'font-size': '15px',
					'width':'40',
					'height':'40'
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
	};

	// Cytoscape edgehandles options
	cyEdgehandlesOptions = {
		preview: false,
		toggleOffOnLeave: true,
		complete: function(sourceNode: any, targetNodes: any[], addedEntities: any[]) {
			var sourceParameters = sourceNode.data().parameters;
			if (!sourceParameters.hasOwnProperty("next"))
				sourceParameters.next = [];

			// The edge handles extension is not integrated into the undo/redo extension.
			// So in order that adding edges is contained in the undo stack,
			// remove the edge just added and add back in again using the undo/redo
			// extension. Also add info to edge which is displayed when user clicks on it.
			for (var i=0; i<targetNodes.length; i++) {
				addedEntities[i].data('parameters', {
					flags: [],
					name: targetNodes[i].data().parameters.name,
					nextStep: targetNodes[i].data().parameters.name,
					temp: true
				});

				//If we attempt to draw an edge that already exists, please remove it and take no further action
				if (sourceParameters.next.find((next: any) => { return next.name === targetNodes[i].data().id })) {
					this.cy.remove(addedEntities);
					return;
				}

				sourceParameters.next.push({
					flags: [],
					status: 'Success',
					name: targetNodes[i].data().id // Note use id, not name since name can be changed
				});

				sourceNode.data('parameters', sourceParameters);
			}

			this.cy.remove(addedEntities);

			_.each(addedEntities, function (ae: any) {
				var data = ae.data();
				delete data.parameters.temp;
				ae.data(data);
			});

			var newEdges = this.ur.do('add',addedEntities); // Added back in using undo/redo extension
		},
	}

	// Simple bootstrap modal params
	modalParams = {
		title: '',
		submitText: '',
		currentPlaybook: '',
		currentWorkflow: '',
		shouldShowPlaybook: false,
		shouldShowExistingPlaybooks: false,
		selectedPlaybook: '',
		newPlaybook: '',
		shouldShowWorkflow: false,
		newWorkflow: '',
	};

	constructor(private playbookService: PlaybookService, private authService: AuthService, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';
		
		this.playbookService.getConditions().then(conditions => this.conditions = conditions);
		this.playbookService.getTransforms().then(transforms => this.transforms = transforms);
		this.playbookService.getDevices().then(devices => this.devices = devices);
		this.playbookService.getActionsForApps().then(actionsForApps => this.actionsForApps = actionsForApps);
		this.getWorkflowResultsSSE();
		this.getPlaybooksWithWorkflows();

		// Register cytoscape plugins
		cytoscapeClipboard(cytoscape); // jquery
		cytoscapeEdgehandles(cytoscape);
		cytoscapeGridGuide(cytoscape); // jquery
		cytoscapePanzoom(cytoscape);
		cytoscapeUndoRedo(cytoscape);
	}

	///------------------------------------
	/// Playbook CRUD etc functions
	///------------------------------------
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
		this.playbookService.loadWorkflow(playbookName, workflowName)
			.then(workflow => {
				this.currentPlaybook = workflowName;
				this.currentWorkflow = playbookName;
				this.loadedWorkflow = workflow;

				// Create the Cytoscape graph
				this.cy = cytoscape(this.cyOptions);

				// Enable various Cytoscape extensions
				// Undo/Redo extension
				this.ur = this.cy.undoRedo({});

				// Panzoom extension
				this.cy.panzoom({});

				// Extension for drawing edges
				this.cy.edgehandles(this.cyEdgehandlesOptions);

				// Extension for copy and paste
				this.cy.clipboard();

				//Extension for grid and guidelines
				this.cy.gridGuide({
					// drawGrid: true,
					// strokeStyle: '#222'
					//options...
				});

				this.cy.fit(50);
		
				this.setStartNode(workflow.start);
		
				// Configure handler when user clicks on node or edge
				this.cy.on('select', 'node', this.onNodeSelect);
				this.cy.on('select', 'edge', this.onEdgeSelect);
				this.cy.on('unselect', this.onUnselect);
		
				// Configure handlers when nodes/edges are added or removed
				this.cy.on('add', 'node', this.onNodeAdded);
				this.cy.on('remove', 'node', this.onNodeRemoved);
				this.cy.on('remove', 'edge', this.onEdgeRemove);
			})
			.catch(e => this.toastyService.error(`Error loading workflow ${playbookName} - ${workflowName}: ${e.message}`));
	}

	saveWorkflow(workflowData: any) {
		if (!this.startNode) {
			this.toastyService.warning(`Workflow cannot be saved without a starting step.`);
			return;
		}

		workflowData = _.filter(workflowData, function (data: any) { return data.group === "nodes"; });

		let steps = _.map(workflowData, function (step: any) {
			var ret = _.cloneDeep(step.data.parameters);
			ret.position = _.clone(step.position);
			return ret;
		});

		// this._transformInputsToSave(steps);

		this.playbookService.saveWorkflow(this.currentPlaybook, this.currentWorkflow, {start: this.startNode, steps: steps })
			.then(() => this.toastyService.success(`Successfully saved workflow ${this.currentPlaybook} - ${this.currentWorkflow}.`))
			.catch(e => this.toastyService.error(`Error saving workflow ${this.currentPlaybook} - ${this.currentWorkflow}: ${e.message}`));
	}

	getPlaybooksWithWorkflows(): void {
		this.playbookService.getPlaybooks()
			.then(playbooks => this.workflowsForPlaybooks = playbooks);
	}

	///------------------------------------
	/// Cytoscape functions
	///------------------------------------
	// This function displays a form next to the graph for editing a node when clicked upon
	onNodeSelect(e: any) {
		let ele = e.cyTarget;
		let parameters = ele.data('parameters');

		this.selectedNode = ele;

		if (this.selectedNode.uid === this.loadedWorkflow.start) parameters.isStartNode = true;
		
		// ele.data('parameters', updatedParameters);
	}

	onEdgeSelect(event: any) {
		return;
	}

	onUnselect(event: any) {
		if (!this.cy.$('node:selected').length) this.selectedNode = null;
	}

	// when an edge is removed, check the edges that still exist and remove the "next" steps for those that don't
	onEdgeRemove(event: any) {
		var edgeData = event.cyTarget.data();
		// Do nothing if this is a temporary edge (edgehandles do not have paramters, and we mark temp edges on edgehandle completion)
		if (!edgeData.parameters || edgeData.parameters.temp) return;

		var parentNode = event.cyTarget.source();
		var parentData = _.cloneDeep(parentNode.data());

		parentData.parameters.next = _.reject(parentData.parameters.next, (next: any) => { return next.name === event.cyTarget.data().target; });
		parentNode.data(parentData);
	}
	
	insertNode(app: string, action: string, x: number, y: number, shouldUseRenderedPosition: boolean): void {
		// Find next available id
		let id = 1;
		while (true) {
			var element = this.cy.getElementById(id.toString());
			if (element.length === 0)
				break;
			id += 1;
		}

		let inputs: { [key: string]: { name: string, value: string } } = {};
		let actionInfo = this.actionsForApps[app].actions[action];
		actionInfo.args.forEach((input: { [key: string]: any }) => {

			var defaultValue;
			if (input.type === "string")
				defaultValue = input.default || "";
			else if (input.type === "boolean")
				defaultValue = input.default || false;
			else
				defaultValue = input.default || 0;

			inputs[input.name] = {
				name: input.name,
				value: defaultValue
			};
		});

		// Add the node with the id just found to the graph in the location dropped
		// into by the mouse.
		let nodeToBeAdded = {
			group: 'nodes',
			data: {
				id: id.toString(),
				label: action,
				parameters: {
					action: action,
					app: app,
					device_id: 0,
					errors: <any[]>[],
					inputs: inputs,
					name: id.toString(),
					next: <any[]>[],
				}
			},
			renderedPosition: <{ x: number, y: number }>null,
			position: <{ x: number, y: number }>null,
		};

		this._setNodeDisplayProperties(nodeToBeAdded);

		if (shouldUseRenderedPosition) nodeToBeAdded.renderedPosition = { x: x, y: y };
		else nodeToBeAdded.position = { x: x, y: y };

		var newNode = this.ur.do('add', nodeToBeAdded);
	}

	_setNodeDisplayProperties(step: any): void {
		//add a type field to handle node styling
		let app = this.actionsForApps[step.data.parameters.app];
		let action = app.actions[step.data.parameters.action];

		if (action.event) step.data.type = 'eventAction';
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
			// var roots = cy.nodes().roots();
			// if (roots.size() > 0) {
			// 	startNode = roots[0].data("parameters").name;
			// }
		}
	}

	removeSelectedNodes(): void {
		var selecteds = this.cy.$(":selected");
		if (selecteds.length > 0)
			this.ur.do("remove", selecteds);
	}

	///------------------------------------
	/// Utility functions
	///------------------------------------
	getPlaybooks(): string[] {
		return Object.keys(this.workflowsForPlaybooks);
	}

	_doesWorkflowExist(playbook: string, workflow: string): boolean {
		if (this.workflowsForPlaybooks.hasOwnProperty(playbook) &&
			this.workflowsForPlaybooks[playbook].indexOf(workflow) >= 0)
			return true;

		return false;
	}

	_doesPlaybookExist(playbook: string): boolean {
		return this.workflowsForPlaybooks.hasOwnProperty(playbook);
	}
}
