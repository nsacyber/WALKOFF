import { Component, ViewEncapsulation, ViewChild, ElementRef, ChangeDetectorRef, OnInit,
	AfterViewChecked, OnDestroy} from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { DatatableComponent } from '@swimlane/ngx-datatable';
import { UUID } from 'angular2-uuid';
import { Observable, interval, timer } from 'rxjs';
import 'rxjs/Rx';
import { plainToClass, classToClass } from 'class-transformer';
import { NgbModal, NgbTabChangeEvent } from '@ng-bootstrap/ng-bootstrap';
import { FormControl } from '@angular/forms';
import { Router } from '@angular/router';

import * as cytoscape from 'cytoscape';
import * as clipboard from 'cytoscape-clipboard';
import * as edgehandles from 'cytoscape-edgehandles';
import * as gridGuide from 'cytoscape-grid-guide';
import * as panzoom from 'cytoscape-panzoom';
import * as undoRedo from 'cytoscape-undo-redo';

import { PlaybookService } from './playbook.service';
import { AuthService } from '../auth/auth.service';
import { UtilitiesService } from '../utilities.service';
import { GlobalsService } from '../globals/globals.service';
import { SettingsService } from '../settings/settings.service';

import { AppApi } from '../models/api/appApi';
import { ActionApi, ActionType } from '../models/api/actionApi';
import { ParameterApi } from '../models/api/parameterApi';
import { ConditionApi } from '../models/api/conditionApi';
import { TransformApi } from '../models/api/transformApi';
import { DeviceApi } from '../models/api/deviceApi';
import { ReturnApi } from '../models/api/returnApi';
import { Workflow } from '../models/playbook/workflow';
import { Action } from '../models/playbook/action';
import { Branch } from '../models/playbook/branch';
import { GraphPosition } from '../models/playbook/graphPosition';
import { Argument, Variant } from '../models/playbook/argument';
import { User } from '../models/user';
import { Role } from '../models/role';
import { NodeStatus, NodeStatuses } from '../models/execution/nodeStatus';
import { ConsoleLog } from '../models/execution/consoleLog';
import { EnvironmentVariable } from '../models/playbook/environmentVariable';
import { PlaybookEnvironmentVariableModalComponent } from './playbook.environment.variable.modal.component';
import { WorkflowStatus } from '../models/execution/workflowStatus';
import { CodemirrorComponent } from '@ctrl/ngx-codemirror';
import { ActivatedRoute } from '@angular/router';
import { Variable } from '../models/variable';
import { MetadataModalComponent } from './metadata.modal.component';
import { Condition } from '../models/playbook/condition';
import { Trigger } from '../models/playbook/trigger';
import { WorkflowNode } from '../models/playbook/WorkflowNode';
import { Transform } from '../models/playbook/transform';
import { VariableModalComponent } from '../globals/variable.modal.component';
import { ResultsModalComponent } from '../execution/results.modal.component';
import { JsonModalComponent } from '../execution/json.modal.component';
import * as io from 'socket.io-client';


@Component({
	selector: 'workflow-editor-component',
	templateUrl: './workflow.editor.html',
	styleUrls: [
		'./workflow.editor.scss',
		'../../../node_modules/cytoscape-panzoom/cytoscape.js-panzoom.css',
		'../../../node_modules/ng2-dnd/bundles/style.css',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [AuthService, GlobalsService, SettingsService],
})
export class WorkflowEditorComponent implements OnInit, AfterViewChecked, OnDestroy {
	@ViewChild('cyRef', { static: true }) cyRef: ElementRef;
	@ViewChild('workflowResultsTable', { static: false }) workflowResultsTable: DatatableComponent;
	@ViewChild('consoleContainer', { static: false }) consoleContainer: ElementRef;
	@ViewChild('consoleTable', { static: false }) consoleTable: DatatableComponent;
	@ViewChild('errorLogTable', { static: false }) errorLogTable: DatatableComponent;
	@ViewChild('environmentVariableTable', { static: false }) environmentVariableTable: DatatableComponent;
	@ViewChild('importFile', { static: false }) importFile: ElementRef;
	@ViewChild('accordion', { static: true }) apps_actions: ElementRef;
	@ViewChild('consoleArea', { static: false }) consoleArea: CodemirrorComponent;

	globals: Variable[] = [];
	relevantGlobals: Variable[] = [];
	users: User[];
	roles: Role[];

	originalWorkflow: Workflow;
	loadedWorkflow: Workflow;
	cy: any;
	edgeHandler: any;
	ur: any;
	appApis: AppApi[] = [];
	offset: GraphPosition = plainToClass(GraphPosition, { x: -330, y: -170 });
	selectedAction: any; // node being displayed in json editor
	selectedActionApi: ActionApi;
	selectedBranchParams: {
		branch: Branch;
		returnTypes: ReturnApi[];
		appName: string;
		actionName: string;
	};
	selectedEnvironmentVariable: EnvironmentVariable;
	cyJsonData: string;
	nodeStatuses: NodeStatus[] = [];
	consoleLog: ConsoleLog[] = [];
	executionResultsComponentWidth: number;
	waitingOnData: boolean = false;
	eventSource: any;
	consoleEventSource: any;
	playbookToImport: File;
	recalculateConsoleTableCallback: any;
	actionFilter: string = '';
	actionFilterControl = new FormControl();
	actionTypes = ActionType;
	showConsole: boolean = false;
	NodeStatuses = NodeStatuses;
	consoleSocket: SocketIOClient.Socket;
	nodeStatusSocket: SocketIOClient.Socket;

	conditionalOptions = {
		tabSize: 4,
		indentUnit: 4,
		mode: 'python',
		placeholder: `# Python to set selected_node to an output action
# For example:
# 		
# if input_1.result > input_2.result:
#     selected_node = output_1
# else:
#     selected_node = output_2`
	}

	transformOptions = {
		tabSize: 4,
		indentUnit: 4,
		mode: 'python',
		placeholder: `# Python to transform previous nodes results using python code
# For example:
# 		
# result = input.result.get("key")`
	}

	constructor(
		private playbookService: PlaybookService, private authService: AuthService,
		private toastrService: ToastrService, private activeRoute: ActivatedRoute,
		private cdr: ChangeDetectorRef, private utils: UtilitiesService,
		private modalService: NgbModal, private router: Router,
		private globalsService: GlobalsService
	) {}

	/**
	 * On component initialization, we grab arrays of globals, app apis, and playbooks/workflows (id, name pairs).
	 * We also initialize an EventSoruce for Action Statuses for the execution results table.
	 * Also initialize cytoscape event bindings.
	 */
	ngOnInit(): void {
		this.initializeCytoscape();
		this.initialLoad();

		/**
		 * Filter app list by application and action names
		 */
		this.actionFilterControl.valueChanges.debounceTime(100).distinctUntilChanged().subscribe(query => {
			this.actionFilter = query.trim();
			setTimeout(() => {
				($('.action-panel') as any)
					.addClass('no-transition')
					.collapse((this.actionFilter) ? 'show' : 'hide')
					.removeClass('no-transition')
			}, 0);
		});
	}

	/**
	 * This angular function is used primarily to recalculate column widths for execution results table.
	 */
	ngAfterViewChecked(): void { }

	/**
	 * Closes our sockets on component destroy.
	 */
	ngOnDestroy(): void {
		if (this.consoleSocket && this.consoleSocket.close) { this.consoleSocket.close(); }
		if (this.nodeStatusSocket && this.nodeStatusSocket.close) { this.nodeStatusSocket.close(); }
	}

	/**
	 * Adds keyboard event bindings for cut/copy/paste/etc.
	 */
	initializeCytoscape(): void {
		const cyDummy = cytoscape();
		if (!cyDummy.clipboard) { clipboard(cytoscape, $); }
		if (!cyDummy.edgehandles) { cytoscape.use(edgehandles); }
		if (!cyDummy.gridGuide) { gridGuide(cytoscape, $); }
		if (!cyDummy.panzoom) { cytoscape.use(panzoom); }
		if (!cyDummy.undoRedo) { cytoscape.use(undoRedo); }
		
		// Handle keyboard presses on graph
		document.addEventListener('keydown', (e: any) => {
			// If we aren't "focused" on a body or button tag, don't do anything
			// to prevent events from being fired while in the parameters editor
			const tagName = document.activeElement.tagName;
			if (!(tagName === 'BODY' || tagName === 'BUTTON')) { return; }
			if (this.cy === null) { return; }

			if (e.which === 46) { // Delete
				this.removeSelectedNodes();
			} else if (e.ctrlKey) {
				//TODO: re-enable undo/redo once we restructure how branches / edges are stored
				// if (e.which === 90) // 'Ctrl+Z', Undo
				//     ur.undo();
				// else if (e.which === 89) // 'Ctrl+Y', Redo
				//     ur.redo();
				if (e.which === 67) {
					// Ctrl + C, Copy
					this.copy();
				} else if (e.which === 86) {
					// Ctrl + V, Paste
					this.paste();
				}
				// else if (e.which === 88) {
				// 	// Ctrl + X, Cut
				// 	this.cut();
				// }
				// else if (e.which == 65) { // 'Ctrl+A', Select All
				//     cy.elements().select();
				//     e.preventDefault();
				// }
			}
		});
	}

		/**
	 * Gets a list of all the loaded playbooks along with their workflows.
	 */
	async initialLoad(): Promise<void> {
		this.globalsService.globalsChange.subscribe(globals => this.globals = globals);
		await this.playbookService.getApis().then(appApis => this.appApis = appApis.sort((a, b) => a.name > b.name ? 1 : -1));

		this.activeRoute.params.subscribe(params => {
			if (params.workflowId) {
				this.playbookService.loadWorkflow(params.workflowId)
					.then(workflow => this.loadWorkflow(workflow))
					.catch(e => this.router.navigateByUrl(`/workflows`))
			}
			else {
				let workflowToCreate: Workflow = this.playbookService.workflowToCreate;
				if (!workflowToCreate) {
					return this.router.navigateByUrl(`/workflows`);
				}
				this.loadWorkflow(workflowToCreate);
			}
		})
	}

		/**
	 * Loads a workflow from a given playbook / workflow name pair and calls function to set up graph.
	 * @param playbook Playbook to load
	 * @param workflow Workflow to load
	 */
	async loadWorkflow(workflow: Workflow): Promise<void> {
		try {
			this.selectWorkflow((workflow.id) ? await this.playbookService.loadWorkflow(workflow.id) : workflow)
		}
		catch(e) {
			this.toastrService.error(`Error loading workflow "${workflow.name}": ${e.message}`)
		}
	}

	selectWorkflow(workflow) {
		this.resetSelections();
		this.initializeActionArguments(workflow);
		this.loadedWorkflow = workflow;
		this.originalWorkflow = workflow.clone();
		this.setupGraph();
	}

	/**
	 * Closes the active workflow and clears all relevant variables.
	 */
	resetSelections(): void {
		this.loadedWorkflow = null;
		this.selectedBranchParams = null;
		this.selectedAction = null;
	}

	initializeActionArguments(workflow: Workflow) {
		workflow.actions.forEach(action => {
			const actionApi = this.getActionApi(action.app_name, action.app_version, action.action_name);
			actionApi.parameters.forEach(parameterApi => {
				const argument = action.arguments.find(a => a.name === parameterApi.name);
				if (!argument) action.arguments.push(this.getDefaultArgument(parameterApi));
			})
		})
	}
	
    ///------------------------------------------------------------------------------------------------------
	/// Console functions
	///------------------------------------------------------------------------------------------------------
	/**
	 * Sets up the Socket for receiving console logs from the server. Binds various events to the event handler.
	 * Will currently return ALL stream actions and not just the ones manually executed.
	 */
	createConsoleSocket(workflowExecutionId: string) {
		if (this.consoleSocket) this.consoleSocket.close();

		this.consoleSocket = this.utils.createSocket('/console', workflowExecutionId);

		this.consoleSocket.on('connected', (data) => {
			const events = plainToClass(ConsoleLog, [
				{ message: `Starting workflow execution....\n`}, 
				...(data as any[])
			]);
			this.consoleLog = [...this.consoleLog, ...events];
			this.updateConsole();
		});

		this.consoleSocket.on('log', (data) => {
			console.log('console', data)
			const consoleEvent = plainToClass(ConsoleLog, data);
			this.consoleLog.push(consoleEvent);
			this.updateConsole();
		});
	}

	updateConsole() {
		this.consoleLog = this.consoleLog.slice();
		if (!this.consoleArea || !this.consoleArea.codeMirror) return;
		const cm = this.consoleArea.codeMirror;
		const $scroller = $(cm.getScrollerElement());
		const atBottom = $scroller[0].scrollHeight - $scroller.scrollTop() - $scroller.outerHeight() <= 0;
		cm.getDoc().setValue(this.consoleContent);
		cm.refresh();
		if (atBottom) cm.execCommand('goDocEnd');
	}

	get consoleContent() {
		return this.consoleLog.map(log => log.message).join('');
	}

	///------------------------------------------------------------------------------------------------------
	/// Node Status functions
	///------------------------------------------------------------------------------------------------------
	/**
	 * Sets up the EventStream for receiving stream actions from the server. Binds various events to the event handler.
	 * Will currently return ALL stream actions and not just the ones manually executed.
	 */

	createNodeStatusSocket(workflowExecutionId: string) {
		if (this.nodeStatusSocket) this.nodeStatusSocket.close();
		this.nodeStatusSocket = this.utils.createSocket('/nodeStatus', workflowExecutionId);

		this.nodeStatusSocket.on('connected', (data) => {
			const events = plainToClass(NodeStatus, (data as any[]));
			events.forEach(event => this.nodeStatusEventHandler(event));
		});

		this.nodeStatusSocket.on('log', (data) => {
			const event = plainToClass(NodeStatus, data);
			console.log('action', event);
			this.nodeStatusEventHandler(event)
		});
	}

	/**
	 * For an incoming action, will try to find the matching action in the graph (if applicable).
	 * Will style nodes based on the action status (executing/success/failure).
	 * Will update the information in the action statuses table as well, adding new rows or updating existing ones.
	 */
	nodeStatusEventHandler(nodeStatus: NodeStatus): void {
		// If we have a graph loaded, find the matching node for this event and style it appropriately if possible.
		if (this.cy) {
			const matchingNode = this.cy.elements(`node[_id="${ nodeStatus.node_id }"]`);
			const nodeType = matchingNode.data('type');
			const incomingEdges = matchingNode.incomers('edge');
			const outgoingEdges = matchingNode.outgoers('edge');

			if (matchingNode) {
				switch (nodeStatus.status) {
					case NodeStatuses.EXECUTING:
						matchingNode.removeClass('success-highlight');
						matchingNode.removeClass('failure-highlight');
						matchingNode.addClass('executing-highlight');
						matchingNode.removeClass('awaiting-data-highlight');
						incomingEdges.addClass(['success-highlight', 'transitioning']);
						setTimeout(() => incomingEdges.removeClass('transitioning'), 500)
						break;
					case NodeStatuses.SUCCESS:
						matchingNode.addClass('success-highlight');
						matchingNode.removeClass('failure-highlight');
						matchingNode.removeClass('executing-highlight');
						matchingNode.removeClass('awaiting-data-highlight');
						if (nodeType != ActionType.CONDITION) {
							outgoingEdges.addClass(['success-highlight', 'transitioning']);
							setTimeout(() => outgoingEdges.removeClass('transitioning'), 500)
						}
						break;
					case NodeStatuses.FAILURE:
						matchingNode.removeClass('success-highlight');
						matchingNode.addClass('failure-highlight');
						matchingNode.removeClass('executing-highlight');
						matchingNode.removeClass('awaiting-data-highlight');
						break;
					case NodeStatuses.AWAITING_DATA:
						matchingNode.removeClass('success-highlight');
						matchingNode.removeClass('failure-highlight');
						matchingNode.removeClass('executing-highlight');
						matchingNode.addClass('awaiting-data-highlight');
					default:
						break;
				}
			}
		}

		// Additionally, add or update the actionstatus in our datatable.
		const matchingNodeStatus = this.nodeStatuses
									   .find(as => as.execution_id === nodeStatus.execution_id && as.node_id == nodeStatus.node_id);
		if (matchingNodeStatus) {
			matchingNodeStatus.status = nodeStatus.status;

			switch (nodeStatus.status) {
				case NodeStatuses.EXECUTING:
					if (!matchingNodeStatus.started_at)
						matchingNodeStatus.started_at = nodeStatus.started_at;
					break;
				case NodeStatuses.SUCCESS:
				case NodeStatuses.FAILURE:
					matchingNodeStatus.completed_at = nodeStatus.completed_at;
					matchingNodeStatus.result = nodeStatus.result;
					break;
				case NodeStatuses.AWAITING_DATA:
					// don't think anything needs to happen here
					break;
				default:
					this.toastrService.warning(`Unknown Action Status Type: ${ nodeStatus.status }.`);
					break;
			}
		} else {
			this.nodeStatuses.push(nodeStatus);
		}
		// Induce change detection by slicing array
		this.nodeStatuses = this.nodeStatuses.slice();
	}

	get selectedActionResults(): any {
		if (this.selectedAction) {
			const nodeStatus = this.nodeStatuses.find(n => n.node_id == this.selectedAction.id);
			if (nodeStatus && nodeStatus.status == NodeStatuses.SUCCESS) return nodeStatus;
		}
	}

	/**
	 * Executes the loaded workflow as it exists on the server. Will not currently execute the workflow as it stands.
	 */
	executeWorkflow(): void {
		if (!this.loadedWorkflow) { return; }
		this.clearExecutionHighlighting();

		const executionId = UUID.UUID();
		Promise.all([
			Promise.resolve(this.createConsoleSocket(executionId)),
			Promise.resolve(this.createNodeStatusSocket(executionId))
		]).then(() => {
			this.playbookService.addWorkflowToQueue(this.loadedWorkflow.id, executionId)
				.then((_: WorkflowStatus) => this.toastrService.success(`Starting <b>${this.loadedWorkflow.name}</b>`))
				.catch(e => this.toastrService.error(`Error starting execution of ${this.loadedWorkflow.name}: ${e.message}`));
		})
	}

	returnToWorkflows() {
		this.router.navigateByUrl(`/workflows`);
		return false;
	}

	routeToWorkflow(workflow: Workflow): void {
		this.router.navigateByUrl(`/workflows/${ workflow.id }`);
	}

	canDeactivate(): Promise<boolean> | boolean {
        return this.checkUnsavedChanges(); 
    }

    async checkUnsavedChanges() : Promise<boolean> {
        if (!this.workflowChanged) return true;
        return this.utils.confirm('Any unsaved changes will be lost. Are you sure?', { alwaysResolve: true });
    }

	setupGraph(options: any = {}): void {
		// Convert our selection arrays to a string
		if (!this.loadedWorkflow.actions) { this.loadedWorkflow.actions = []; }

		// Refresh the console log so that it displays correctly after being hidden
		setTimeout(() => {
			if (this.consoleArea && this.consoleArea.codeMirror) this.consoleArea.codeMirror.refresh();
		});

		const defaults = {
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
						'width': 'label',
						'height': 'label',
						'padding': '10px'
					},
				},
				{
					selector: `node[type="${ ActionType.ACTION }"]`,
					css: {
						'shape': 'roundrectangle',
						'padding': '15px'
					},
				},
				{
					selector: `node[type="${ ActionType.CONDITION }"]`,
					css: {
						'shape': 'diamond',
						'padding': '25px'
					},
				},
				{
					selector: `node[type="${ ActionType.TRIGGER }"]`,
					css: {
						'shape': 'polygon',
						'shape-polygon-points': '-1, -1, 1, -1, 0, 1',
						'text-margin-y': '-15px',
						'padding': '25px'
					},
				},
				{
					selector: `node[type="${ ActionType.TRANSFORM }"]`,
					css: {
						'shape': 'ellipse',
						'padding': '20px'
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
						'border-width': '3px',
						'border-color': '#991818',
					},
				},
				{
					selector: `node[?isParallelized]`,
					css: {
						'ghost' : 'yes',
						'ghost-offset-x' : '7px',
						'ghost-offset-y': '-7px',
						'ghost-opacity' : '.7'
					},
				},
				{
					selector: 'node[?hasErrors]',
					css: {
						'color': '#991818',
						'font-style': 'italic',
					},
				},
				{
					selector: 'node:selected',
					css: {
						'background-color': '#77b0d0',
					},
				},
				{
					selector: '.success-highlight',
					css: {
						'background-color': '#399645',
						'transition-property': 'background-color',
						'transition-duration': '0.5s',
					},
				},
				{
					selector: '.failure-highlight',
					css: {
						'background-color': '#8e3530',
						'transition-property': 'background-color',
						'transition-duration': '0.5s',
					},
				},
				{
					selector: '.executing-highlight',
					css: {
						'background-color': '#ffef47',
						'transition-property': 'background-color',
						'transition-duration': '0.25s',
					},
				},
				{
					selector: '.awaiting-data-highlight',
					css: {
						'background-color': '#f4ad42',
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
				{
					selector: 'edge.transitioning',
					css: {
						'transition-property': 'line-color, width',
						'transition-duration': '0.5s',
					},
				},
				{
					selector: 'edge.executing-highlight',
					css: {
						'width': '5px',
						'target-arrow-color': '#ffef47',
						'line-color': '#ffef47',
					},
				},
				{
					selector: 'edge.success-highlight',
					css: {
						'width': '5px',
						'target-arrow-color': '#399645',
						'line-color': '#399645',
					},
				},
				{
					selector: 'edge[?hasErrors]',
					css: {
						'target-arrow-color': '#991818',
						'line-color': '#991818',
						'line-style': 'dashed'
					},
				},
				{
					selector: '.eh-handle',
					style: {
						'background-color': '#337ab7',
						'width': '1',
						'height': '1',
						'shape': 'ellipse',
						'overlay-opacity': '0',
					}
				},
				{
					selector: '.eh-source',
					style: {
						'border-width': '3',
						'border-color': '#337ab7'
					}
				},
				{
					selector: '.eh-target',
					style: {
						'border-width': '3',
						'border-color': '#337ab7'
					}
				},
				{
					selector: '.eh-preview, .eh-ghost-edge',
					style: {
						'background-color': '#337ab7',
						'line-color': '#337ab7',
						'target-arrow-color': '#337ab7',
						'source-arrow-color': '#337ab7'
					}
				}
			],
		};

		// Create the Cytoscape graph
		cytoscape.warnings(false);

		// Create new elements before recreating the new graph
		const elements = this.getGraphElements();

		this.cy = cytoscape(Object.assign({}, defaults, options));

		// Enable various Cytoscape extensions
		// Undo/Redo extension
		this.ur = this.cy.undoRedo({});
		this.ur.action('add-walkoff-node', args => this.insertNodes(args), args => this.removeNodes(args));
		this.ur.action('remove-walkoff-node', args => this.removeNodes(args), args => this.insertNodes(args));


		// Panzoom extension
		this.cy.panzoom({});

		// Extension for drawing edges
		this.edgeHandler = this.cy.edgehandles({
			handleNodes: (el) => el.isNode() && !el.hasClass('just-created'),
			preview: false,
			toggleOffOnLeave: true,
			complete: (sourceNode: any, targetNodes: any[], addedEntities: any[]) => {
				if (!this.loadedWorkflow.branches) { this.loadedWorkflow.branches = []; }

				// The edge handles extension is not integrated into the undo/redo extension.
				// So in order that adding edges is contained in the undo stack,
				// remove the edge just added and add back in again using the undo/redo
				// extension. Also add info to edge which is displayed when user clicks on it.
				for (let i = 0; i < targetNodes.length; i++) {
					const tempId = UUID.UUID();
					const sourceId: string = sourceNode.data('_id');
					const destinationId: string = targetNodes[i].data('_id');

					addedEntities[i].data({
						_id: tempId,
						// We set temp because this actually triggers onEdgeRemove since we manually remove and re-add the edge later
						// There is logic in onEdgeRemove to bypass that logic if temp is true
						temp: true,
					});

					//If we attempt to draw an edge that already exists, please remove it and take no further action
					if (this.loadedWorkflow.branches.find(b => b.source_id === sourceId && b.destination_id === destinationId)) {
						this.cy.remove(addedEntities);
						return;
					}

					const sourceAction = this.loadedWorkflow.nodes.find(a => a.id === sourceId);
					const sourceActionApi = this.getActionApi(sourceAction.app_name, sourceAction.app_version, sourceAction.action_name);

					// Get our default status either from the default return if specified, or the first return status
					let defaultStatus = '';
					if (sourceActionApi.default_return) {
						defaultStatus = sourceActionApi.default_return;
					} else if (sourceActionApi.returns && sourceActionApi.returns.length) {
						defaultStatus = sourceActionApi.returns[0].status;
					}

					const newBranch = new Branch();

					newBranch.id = tempId;
					newBranch.source_id = sourceId;
					newBranch.destination_id = destinationId;

					// Add our branch to the actual loadedWorkflow model
					this.loadedWorkflow.branches.push(newBranch);

					targetNodes[i].addClass('just-created');
				}

				this.cy.remove(addedEntities);

				// Get rid of our temp flag
				addedEntities.forEach(ae => ae.data('temp', false));

				// Re-add with the undo-redo extension.
				this.ur.do('add', addedEntities); // Added back in using undo/redo extension

			},
		});

		// Extension for copy and paste
		this.cy.clipboard();

		//Extension for grid and guidelines
		this.cy.gridGuide({
			snapToGridDuringDrag: true,
			zoomDash: true,
			panGrid: true,
			centerToEdgeAlignment: true,
			distributionGuidelines: true, // Distribution guidelines
			geometricGuideline: true, // Geometric guidelines
			// Guidelines
			guidelinesStackOrder: 4, // z-index of guidelines
			guidelinesTolerance: 2.00, // Tolerance distance for rendered positions of nodes' interaction.
			guidelinesStyle: { // Set ctx properties of line. Properties are here:
				strokeStyle: '#8b7d6b', // color of geometric guidelines
				geometricGuidelineRange: 400, // range of geometric guidelines
				range: 100, // max range of distribution guidelines
				minDistRange: 10, // min range for distribution guidelines
				distGuidelineOffset: 10, // shift amount of distribution guidelines
				horizontalDistColor: '#ff0000', // color of horizontal distribution alignment
				verticalDistColor: '#00ff00', // color of vertical distribution alignment
				initPosAlignmentColor: '#0000ff', // color of alignment to initial mouse location
				lineDash: [0, 0], // line style of geometric guidelines
				horizontalDistLine: [0, 0], // line style of horizontal distribution guidelines
				verticalDistLine: [0, 0], // line style of vertical distribution guidelines
				initPosAlignmentLine: [0, 0], // line style of alignment to initial mouse position
			},
		});

		this.cy.add(elements);

		if(!options.zoom || !options.pan) setImmediate(() => this.cy.fit(null, 75));

		this.setStartNode(this.loadedWorkflow.start);

		// Note: these bindings need to use arrow notation
		// to actually be able to use 'this' to refer to the PlaybookComponent.
		// Configure handler when user clicks on node or edge
		this.cy.on('select', 'node', (e: any) => this.onNodeSelect(e));
		this.cy.on('select', 'edge', (e: any) => this.onEdgeSelect(e));
		this.cy.on('unselect', (e: any) => this.onUnselect(e));
		this.cy.on('select unselect', (e: any) => this.triggerCanvasResize());

		// Configure handlers when nodes/edges are added or removed
		this.cy.on('add', 'node', (e: any) => this.onNodeAdded(e));
		this.cy.on('free', 'node', (e: any) => this.onNodeMoved(e));
		this.cy.on('remove', 'node', (e: any) => this.onNodeRemoved(e));
		this.cy.on('remove', 'edge', (e: any) => this.onEdgeRemove(e));

		// Allow right clicking to create an edge
		this.cy.on('mouseover mouseout', 'node', (e: any) => e.target.removeClass('just-created'));
		this.cy.on('cxttapstart', 'node', (e: any) => this.edgeHandler.start(e.target));
		this.cy.on('cxttapend', 'node', (e: any) => this.edgeHandler.stop());
		this.cy.on('cxtdragover', 'node', (e: any) => this.edgeHandler.preview(e.target));
		this.cy.on('cxtdragout', 'node', (e: any) => {
			if (this.edgeHandler.options.snap && e.target.same(this.edgeHandler.targetNode)) {
				// then keep the preview
			} else {
				this.edgeHandler.unpreview(e.target);
			}
		})

		// this.cyJsonData = JSON.stringify(this.loadedWorkflow, null, 2);
	}

	// Load the data into the graph
	getGraphElements() {
		// If a node does not have a label field, set it to
		// the action. The label is what is displayed in the graph.
		const edges = this.loadedWorkflow.branches.map(branch => {
			const edge: any = { group: 'edges' };
			edge.data = {
				id: branch.id,
				_id: branch.id,
				source: branch.source_id,
				target: branch.destination_id,
				hasErrors: branch.has_errors
			};
			return edge;
		});

		const nodes = this.loadedWorkflow.nodes.map(action => {
			const node: any = { group: 'nodes', position: this.utils.cloneDeep(action.position) };
			node.data = {
				id: action.id,
				_id: action.id,
				label: action.name,
				isStartNode: action.id === this.loadedWorkflow.start,
				isParallelized: action instanceof Action && action.parallelized,
				hasErrors: action.has_errors,
				type: action.action_type
			};
			return node;
		});

		const elements = [].concat(nodes, edges);
		const oldElements = (this.cy) ? this.cy.elements().jsons() : [];
		oldElements.filter(old => old.classes).forEach(old => {
			elements
				.filter(el => el.data.id == old.data.id)
				.forEach(el => el.classes = old.classes.replace('transitioning', ''))
		})

		return elements;
	}

	/**
	 * Triggers the save action based on the editor option selected.
	 */
	save(): void {
		this.saveWorkflow(this.cy.elements().jsons());
	}

	/**
	 * Saves the workflow loaded in the editor.
	 * Updates the graph positions from the cytoscape model and sanitizes data beforehand.
	 * @param cyData Nodes and edges from the cytoscape graph. Only really used to grab the new positions of nodes.
	 */
	saveWorkflow(cyData: any[]): void {
		// Unselect anything selected first (will trigger onUnselect)
		this.cy.$(':selected').unselect();

		// Clone the loadedWorkflow first, so we don't change the parameters
		// in the editor when converting it to the format the backend expects.
		const workflowToSave: Workflow = classToClass(this.loadedWorkflow, { ignoreDecorators: true });

		if (!workflowToSave.start) {
			this.toastrService.warning('Workflow cannot be saved without a starting action.');
			return;
		}

		// Go through our workflow and update some parameters
		workflowToSave.nodes.forEach(action => {
			// Set action name if empty
			if (!action.name) action.name = workflowToSave.getNextActionName(action.action_name);

			// Set the new cytoscape positions on our loadedworkflow
			action.position = cyData.find(cyAction => cyAction.data._id === action.id).position;

			// Properly sanitize arguments through the tree
			if (action.arguments) this._sanitizeArgumentsForSave(action, workflowToSave);
		});

		if (this.loadedWorkflow.id) {
			this.playbookService.saveWorkflow(workflowToSave).then(savedWorkflow => {
				this.selectWorkflow(savedWorkflow);
				this.toastrService.success(`Saved <b>${ savedWorkflow.name }</b>`);
			}).catch(e => this.toastrService.error(`Error saving workflow ${workflowToSave.name}: ${e.message}`));
		} else {
			this.playbookService.newWorkflow(workflowToSave).then(savedWorkflow => {
				this.selectWorkflow(savedWorkflow);
				this.toastrService.success(`Saved <b>${ savedWorkflow.name }</b>`);
				this.router.navigateByUrl(`/workflows/${ savedWorkflow.id }`);
			}).catch(e => this.toastrService.error(`Error saving workflow ${workflowToSave.name}: ${e.message}`));
		}

		this.clearExecutionResults();
	}

	/**
	 * Sanitizes an argument so we don't have bad data on save, such as a value when reference is specified.
	 * @param argument The argument to sanitize
	 */
	_sanitizeArgumentsForSave(action: WorkflowNode, workflow: Workflow): void {
		const args = action.arguments;

		// Filter out any arguments that are blank, essentially
		const idsToRemove: number[] = [];
		for (const argument of args) {
			// First trim any string inputs for sanitation and so we can check against ''
			if (typeof (argument.value) === 'string') { argument.value = argument.value.trim(); }

			// If value and reference are blank, add this argument's ID in the array to the list
			// Add them in reverse so we don't have problems with the IDs sliding around on the splice
			if (!argument.value && argument.value !== false) {
				idsToRemove.unshift(args.indexOf(argument));
			}

			// Make sure reference is valid for this action
			if (argument.variant == Variant.ACTION_RESULT) {
				const validReferences = workflow.getPreviousActions(action).map(a => a.id);
				if (!validReferences.includes(argument.value)) {
					idsToRemove.unshift(args.indexOf(argument));
				}
			}
		}
		// Actually splice out all the args
		for (const id of idsToRemove) {
			args.splice(id, 1);
		}
	}

	///------------------------------------------------------------------------------------------------------
	/// Cytoscape functions
	///------------------------------------------------------------------------------------------------------

	/**
	 * This function displays a form next to the graph for editing a node when clicked upon
	 * @param e JS Event fired
	 */
	onNodeSelect(e: any): void {
		this.selectedBranchParams = null;

		const data = e.target.data();

		// Unselect anything else we might have selected (via ctrl+click basically)
		this.cy.elements(`[_id!="${data._id}"]`).unselect();

		const action = this.loadedWorkflow.nodes.find(a => a.id === data._id);
		if (!action) { return; }
		const actionApi = this.getActionApi(action.app_name, action.app_version, action.action_name);

		const queryPromises: Array<Promise<any>> = [];

		if (!this.users &&
			(actionApi.parameters.findIndex(p => p.json_schema.type === 'user') > -1 ||
			actionApi.parameters.findIndex(p => p.json_schema.items && p.json_schema.items.type === 'user') > -1)) {
			this.waitingOnData = true;
			queryPromises.push(this.playbookService.getUsers().then(users => this.users = users));
		}
		if (!this.roles &&
			(actionApi.parameters.findIndex(p => p.json_schema.type === 'role') > -1 ||
			actionApi.parameters.findIndex(p => p.json_schema.items && p.json_schema.items.type === 'role') > -1)) {
			this.waitingOnData = true;
			queryPromises.push(this.playbookService.getRoles().then(roles => this.roles = roles));
		}

		if (queryPromises.length) {
			Promise.all(queryPromises)
				.then(() => {
					this.waitingOnData = false;
				})
				.catch(error => {
					this.waitingOnData = false;
					this.toastrService.error(`Error grabbing users or roles: ${error.message}`);
				});
		}

		this.selectedAction = action;
		this.selectedActionApi = actionApi;

		// TODO: maybe scope out relevant globals by action, but for now we're just only scoping out by app
		this.relevantGlobals = this.globals; //.filter(d => d.app_name === this.selectedAction.app_name);
	}

	/**
	 * This function displays a form next to the graph for editing an edge when clicked upon.
	 * @param e JS Event fired
	 */
	onEdgeSelect(e: any): void {
		this.selectedAction = null;
		this.selectedBranchParams = null;

		const id: string = e.target.data('_id');

		// Unselect anything else we might have selected (via ctrl+click basically)
		this.cy.elements(`[_id!="${id}"]`).unselect();

		const branch = this.loadedWorkflow.branches.find(b => b.id === id);
		const sourceAction = this.loadedWorkflow.nodes.find(a => a.id === branch.source_id);

		this.selectedBranchParams = {
			branch,
			returnTypes: this.getActionApi(sourceAction.app_name, sourceAction.app_version, sourceAction.action_name).returns,
			appName: sourceAction.app_name,
			actionName: sourceAction.action_name,
		};
	}

	/**
	 * This function unselects any selected nodes/edges and updates the label if necessary.
	 * @param e JS Event fired
	 */
	onUnselect(event: any): void {
		// Update our labels if possible
		if (this.selectedAction) {
			this.cy.elements(`node[_id="${this.selectedAction.id}"]`).data('label', this.selectedAction.name);
		}

		if (!this.cy.$(':selected').length) {
			this.selectedAction = null;
			this.selectedBranchParams = null;
		}
	}

	/**
	 * This function checks when an edge is removed and removes branches as appropriate.
	 * @param e JS Event fired
	 */
	onEdgeRemove(event: any): void {
		const edgeData = event.target.data();
		// Do nothing if this is a temporary edge
		// (edgehandles do not have paramters, and we mark temp edges on edgehandle completion)
		if (!edgeData || edgeData.temp) { return; }

		const sourceId: string = edgeData.source;
		const destinationId: string = edgeData.target;

		// Filter out the one that matches
		this.loadedWorkflow.branches = this.loadedWorkflow.branches
			.filter(b => !(b.source_id === sourceId && b.destination_id === destinationId));
	}

	/**
	 * This function checks when a node is added and sets start node if no other nodes exist.
	 * @param e JS Event fired
	 */
	onNodeAdded(event: any): void {
		const node = event.target;

		// If the number of nodes in the graph is one, set the start node to it.
		if (node.isNode() && this.cy.nodes().size() === 1) { this.setStartNode(node.data('_id')); }
	}

	/**
	 * This function checks when a node is added and sets start node if no other nodes exist.
	 * @param e JS Event fired
	 */
	onNodeMoved(event: any): void {
		const node = event.target.json();
		this.loadedWorkflow.nodes.find(n => n.id == node.data.id).position = node.position;
	}

	/**
	 * This function fires when a node is removed. If the node was the start node, it sets it to a new root node.
	 * It also removes the corresponding action from the workflow.
	 * @param e JS Event fired
	 */
	onNodeRemoved(event: any): void {
		const node = event.target, data = node.data();

		// If the start node was deleted, set it to one of the roots of the graph
		if (data && node.isNode() && this.loadedWorkflow.start === data._id) { this.setStartNode(null); }
		if (this.selectedAction && this.selectedAction.id === data._id) { this.selectedAction = null; }

		// Delete the action from the workflow and delete any branches that reference this action
		this.loadedWorkflow.removeNode(data._id);
	}

	/**
	 * This function fires when an action is dropped onto the graph and fires the insertNode function.
	 * @param e JS Event fired
	 */
	handleDropEvent(e: any): void {
		if (this.cy === null) { return; }
		const nodes = [ this.createWorkflowNode(e.dragData.actionApi, this.createPosition(e.mouseEvent.layerX, e.mouseEvent.layerY)) ];
		this.ur.do('add-walkoff-node', { nodes })
	}

	/**
	 * This function is fired when an action on the left-hand list is double clicked.
	 * It drops a new node of that action in the center of the visible graph.
	 * @param appName App name the action resides under
	 * @param actionName Name of the action that was double clicked
	 */
	handleDoubleClickEvent(actionApi: ActionApi): void {
		if (this.cy === null) { return; }
		const nodes = [ this.createWorkflowNode(actionApi, this.getCenterPosition()) ];
		this.ur.do('add-walkoff-node', { nodes })
	}

	createPosition(x: number, y: number) : GraphPosition {
		const pan = this.cy.pan(), zoom = this.cy.zoom();
		return plainToClass(GraphPosition, {
			x: (x - pan.x) / zoom,
			y: (y - pan.y) / zoom,
		});
	}

	getCenterPosition(): GraphPosition {
		const extent = this.cy.extent(), avg = (a: number, b: number) => (a + b) / 2;
		return plainToClass(GraphPosition, { x: avg(extent.x1, extent.x2), y: avg(extent.y1, extent.y2) });
	}

	/**
	 * Inserts node into the graph and adds a corresponding action to the loadedworkflow.
	 * @param appName App name the action resides under
	 * @param actionName Name of the action to add
	 * @param location Graph Position, where to create the node
	 * @param shouldUseRenderedPosition Whether or not to use rendered or "real" graph position
	 */
	insertNodes({nodes = [], branches = []}: { nodes: WorkflowNode[], branches: Branch[] }) {
		nodes.forEach(node => {
			this.loadedWorkflow.addNode(node);
			this.cy.add({ 
				group: 'nodes', 
				position: this.utils.cloneDeep(node.position),
				data: {
					id: node.id,
					_id: node.id,
					label: node.name,
					isStartNode: node.id === this.loadedWorkflow.start,
					isParallelized: node instanceof Action && node.parallelized,
					hasErrors: node.has_errors,
					type: node.action_type
				}
			});
		});

		branches.forEach(branch => {
			this.loadedWorkflow.branches.push(branch);
			this.cy.add({ 
				group: 'edges', 
				data: {
					id: branch.id,
					_id: branch.id,
					source: branch.source_id,
					target: branch.destination_id,
					hasErrors: branch.has_errors
				}
			});
		});

		return { nodes, branches };
	}

	removeNodes({nodes = [], branches = []}: { nodes: WorkflowNode[], branches: Branch[] }) {
		nodes.forEach(node => {
			this.loadedWorkflow.branches
				.filter(b => b.source_id === node.id || b.destination_id === node.id)
				.filter(b => !branches.includes(b))
				.forEach(b => branches.push(b))

			this.cy.elements(`[_id="${ node.id }"]`).remove();
		});

		branches.forEach(branch => {
			this.cy.elements(`[_id="${ branch.id }"]`).remove();
		});

		return { nodes, branches };
	}

	createWorkflowNode(actionApi: ActionApi, position: GraphPosition, id: string = null): WorkflowNode {
		const args: Argument[] = [];

		// TODO: might be able to remove this entirely
		// due to the argument component auto-initializing default values
		if (actionApi && actionApi.parameters) {
			actionApi.parameters.forEach((parameter) => {
				args.push(this.getDefaultArgument(parameter));
			});
		}

		let node: WorkflowNode;
		switch(actionApi.node_type) {
			case ActionType.CONDITION:
				node = new Condition();
				break;
			case ActionType.TRIGGER:
				node = new Trigger();
				break;
			case ActionType.TRANSFORM:
				node = new Transform();
				break;
			default:
				node = new Action();
		}

		node.id = id ? id : UUID.UUID();
		node.name = this.loadedWorkflow.getNextActionName(actionApi.name);
		node.app_name = actionApi.app_name;
		node.app_version = actionApi.app_version;
		node.action_name = actionApi.name;
		node.arguments = args;
		node.position = position;

		return node;
	}

	// TODO: update this to properly "cut" actions from the loadedWorkflow.
	/**
	 * Cytoscape cut method.
	 */
	// cut(): void {
	// 	const selecteds = this.cy.$(':selected');
	// 	if (selecteds.length > 0) {
	// 		this.cy.clipboard().copy(selecteds);
	// 		this.ur.do('remove', selecteds);
	// 	}
	// }

	/**
	 * Cytoscape copy method.
	 */
	copy(): void {
		this.cy.clipboard().copy(this.cy.$(':selected'));
	}

	/**
	 * Cytoscape paste method.
	 */
	paste(): void {
		const newNodes = this.ur.do('paste');

		newNodes.forEach((n: any) => {
			// Get a copy of the action we just copied
			const pastedAction = this.loadedWorkflow.nodes.find(a => a.id === n.data('_id')).clone();
			const newActionUuid = UUID.UUID();

			pastedAction.id = newActionUuid;
			pastedAction.name = this.loadedWorkflow.getNextActionName(pastedAction.action_name)
			pastedAction.arguments.forEach(argument => delete argument.id);
			this.loadedWorkflow.addNode(pastedAction);

			n.data({
				id: newActionUuid,
				_id: newActionUuid,
				label: pastedAction.name,
				isStartNode: false,
			});
			n.emit('select');
		});
	}

	/**
	 * Clears execution results table and execution highlighting
	 */
	clearExecutionResults() {
		this.clearExecutionHighlighting();
		this.consoleLog = [];
		this.nodeStatuses = [];
		if (this.consoleArea && this.consoleArea.codeMirror) 
			this.consoleArea.codeMirror.getDoc().setValue('');
	}

	/**
	 * Clears the red/green highlighting in the cytoscape graph.
	 */
	clearExecutionHighlighting(): void {
		this.cy.elements().removeClass('success-highlight failure-highlight executing-highlight transitioning');
	}

	/**
	 * Sets the start action / node to be the one matching the ID specified.
	 * Not specifying a ID just grabs the first root.
	 * @param start DB ID of the new start node (optional)
	 */
	setStartNode(start: string): void {
		// If no start was given set it to one of the root nodes
		if (start) {
			this.loadedWorkflow.start = start;
		} else {
			const roots = this.cy.nodes().roots();
			if (roots.size() > 0) {
				this.loadedWorkflow.start = roots[0].data('_id');
			}
		}

		// Clear start node highlighting of the previous start node(s)
		this.cy.elements('node[?isStartNode]').data('isStartNode', false);
		// Apply start node highlighting to the new start node.
		this.cy.elements(`node[_id="${ this.loadedWorkflow.start }"]`).data('isStartNode', true);
	}

	updateParallelizedNode(action: Action): void {
		this.cy.elements(`node[_id="${ action.id }"]`).data('isParallelized', action.parallelized);
	}

	/**
	 * Removes all selected nodes and edges.
	 */
	removeSelectedNodes(): void {
		const selected = this.cy.$(':selected'), nodes = [], branches = [];

		selected.nodes().jsons().forEach(i => {
			const node = this.loadedWorkflow.nodes.find(n => i.data._id == n.id);
			if (node) nodes.push(node);
		})
		selected.edges().jsons().forEach(i => {
			const branch = this.loadedWorkflow.branches.find(b => i.data._id == b.id);
			if (branch) branches.push(branch);
		})

		// Unselect the elements first to remove the parameters editor if need be
		// Because deleting elements doesn't unselect them for some reason
		this.cy.elements(':selected').unselect();
		if (selected.length > 0) this.ur.do('remove-walkoff-node', { nodes, branches });
	}

	///------------------------------------------------------------------------------------------------------
	/// Utility functions
	///------------------------------------------------------------------------------------------------------

	/**
	 * Gets an ActionApi object by app and action name
	 * @param appName App name the action resides under
	 * @param actionName Name of the ActionApi to query
	 */
	getActionApi(appName: string, appVersion: string, actionName: string): ActionApi {
		//return this.appApis.find(a => a.name === appName).action_apis.find(a => a.name === actionName);
		return this.appApis.find(a => a.name === appName && a.app_version == appVersion)
				.action_apis.find(a => a.name === actionName);
	}

	/**
	 * Gets a given argument matching an inputted parameter API.
	 * Adds a new argument to the selected action with default values if the argument doesn't exist.
	 * @param parameterApi Parameter API object relating to the argument to return
	 */
	getActionArgument(parameterApi: ParameterApi): Argument {
		// Find an existing argument
		if (!this.selectedAction.arguments) this.selectedAction.arguments = [];
		let argument = this.selectedAction.arguments.find(a => a.name === parameterApi.name);
		if (argument) { return argument; }

		argument = this.getDefaultArgument(parameterApi);
		this.selectedAction.arguments.push(argument);
		return argument;
	}

	/**
	 * Returns an argument based upon a given parameter API and its default value.
	 * @param parameterApi Parameter API used to generate the default argument
	 */
	getDefaultArgument(parameterApi: ParameterApi): Argument {
		let initialValue = null;
		if (parameterApi.json_schema.type === 'array') {
			initialValue = [];
		} else if (parameterApi.json_schema.type === 'object') {
			initialValue = {};
		} else if (parameterApi.json_schema.type === 'boolean') {
			initialValue = false;
		}

		return plainToClass(Argument, {
			name: parameterApi.name,
			variant: Variant.STATIC_VALUE,
			value: (parameterApi.json_schema.default) ? parameterApi.json_schema.default : initialValue,
		});
	}

	/**
	 * Gets a list of ConditionApis from a given app name.
	 * @param appName App name to query
	 */
	getConditionApis(appName: string): ConditionApi[] {
		return this.appApis.find(a => a.name === appName).condition_apis;
	}

	/**
	 * Gets a list of TransformApis from a given app name.
	 * @param appName App name to query
	 */
	getTransformApis(appName: string): TransformApi[] {
		return this.appApis.find(a => a.name === appName).transform_apis;
	}

	/**
	 * Gets a list of TransformApis from a given app name.
	 * @param appName App name to query
	 */
	getGlobalApis(appName: string): DeviceApi[] {
		return this.appApis.find(a => a.name === appName).device_apis;
	}

	/**
	 * Gets an parameterApi matching the app, action, and input names specified.
	 * @param appName App name the ActionApi resides under
	 * @param actionName Name of the ActionApi to query
	 * @param inputName Name of the action input to query
	 */
	getInputApiArgs(appName: string, appVersion: string, actionName: string, inputName: string): ParameterApi {
		return this.getActionApi(appName, appVersion, actionName).parameters.find(a => a.name === inputName);
	}

	/**
	 * Filters only the apps that have actions specified
	 */
	getAppsWithActions(): AppApi[] {
		return this.appApis.filter(a => a.action_apis && a.getFilteredActionApis(this.actionFilter).length);
	}

	/**
	 * Removes the white space in a given string.
	 * @param input Input string to remove the whitespace of
	 */
	removeWhitespace(input: string): string {
		return input.replace(/\s/g, '');
	}

	get workflowChanged(): boolean {
		return this.loadedWorkflow && 
			(!this.loadedWorkflow.id || JSON.stringify(this.originalWorkflow).localeCompare(JSON.stringify(this.loadedWorkflow)) != 0);
	}

	/**
	 * Returns errors in the loaded workflow
	 */
	getErrors() : any[] {
		if (!this.loadedWorkflow) return [];
		return this.loadedWorkflow.all_errors.map(error => ({ error }));
	}

	toggleConsole() {
		this.showConsole = ! this.showConsole;
		this.triggerCanvasResize();
	}

	switchConsoleTabs($e: NgbTabChangeEvent) {
		if ($e.nextId == 'menu-tab' ) return $e.preventDefault();

		this.showConsole = true;
		this.triggerCanvasResize();
		setTimeout(() => this.recalculateConsoleTable($e), 255);
	}

	/**
	 * This function is used primarily to recalculate column widths for execution results table.
	 */
	recalculateConsoleTable($e: NgbTabChangeEvent) {
		let table: DatatableComponent;
		setImmediate(() => {
			switch($e.nextId) {
				case 'console-tab':
					table = this.consoleTable;
					break;
				case 'execution-tab':
					table = this.workflowResultsTable;
					break;
				case 'error-tab':
					table = this.errorLogTable;
					break;
				case 'variable-tab':
					table = this.environmentVariableTable;
					break;
			}

			if (table && table.recalculate) {
				console.log('changing: ' + $e.nextId)
				this.cdr.detectChanges();
				if (Array.isArray(table.rows)) table.rows = [...table.rows];
				table.recalculate();
			}
		})
	}

	/**
	 * Returns errors in the loaded workflow
	 */
	getVariables() : any[] {
		if (!this.loadedWorkflow) return [];
		return this.loadedWorkflow.environment_variables;
	}

	/**
	 * Returns errors in the loaded workflow
	 */
	deleteVariable(selectedVariable: EnvironmentVariable) {
		this.loadedWorkflow.deleteVariable(selectedVariable);
		if (this.loadedWorkflow.environment_variables.length == 0)
			($('.nav-tabs a[href="#console"], a[href="#errorLog"]') as any).tab('show');
	}

	editVariableModal(selectedVariable: EnvironmentVariable) {
		const modalRef = this.modalService.open(PlaybookEnvironmentVariableModalComponent);
		modalRef.componentInstance.existing = true;
		modalRef.componentInstance.variable = selectedVariable;
		modalRef.result.then(variable => {
			this.loadedWorkflow.environment_variables = this.loadedWorkflow.environment_variables.slice();
		}).catch(() => null)
	}

	onCreateVariable(argument: Argument) {
		const modalRef = this.modalService.open(PlaybookEnvironmentVariableModalComponent);
		modalRef.result.then(variable => {
			if (!this.loadedWorkflow.environment_variables) this.loadedWorkflow.environment_variables = [];
			this.loadedWorkflow.environment_variables.push(variable);
			this.loadedWorkflow.environment_variables = this.loadedWorkflow.environment_variables.slice();
			argument.value = variable.id;
		}).catch(() => argument.value = '')
	}

	workflowVariablesModal() {
		const modalRef = this.modalService.open(PlaybookEnvironmentVariableModalComponent);
		modalRef.result.then(variable => {
			if (!this.loadedWorkflow.environment_variables) this.loadedWorkflow.environment_variables = [];
			this.loadedWorkflow.environment_variables.push(variable);
			this.loadedWorkflow.environment_variables = this.loadedWorkflow.environment_variables.slice();
		}).catch(() => null)
	}

	resultsModal(results) {
		const modalRef = this.modalService.open(JsonModalComponent, { size: 'lg', centered: true });
		modalRef.componentInstance.results = results;
		return false;
	}

	/**
	 * Spawns a modal for adding a new global. Passes in the app names and apis for usage in the modal.
	 */
	addGlobal(): void {
		const modalRef = this.modalService.open(VariableModalComponent);
		modalRef.componentInstance.isGlobal = true;

		modalRef.result.then(variable => {
			this.globalsService.addGlobal(variable).then(() => {
				this.toastrService.success(`Added <b>${variable.name}</b>`);
			})
		}, () => null)
	}

	/**
	 * Spawns a modal for editing an existing global. Passes in the app names and apis for usage in the modal.
	 */
	editGlobal(global: Variable): void {
		const modalRef = this.modalService.open(VariableModalComponent);
		modalRef.componentInstance.isGlobal = true;
		modalRef.componentInstance.existing = true;
		modalRef.componentInstance.variable = global.clone();
		
		modalRef.result.then(variable => {
			this.globalsService.editGlobal(variable).then(() => {
				this.toastrService.success(`Updated <b>${variable.name}</b>`);
			})
		}, () => null)
	}

	/**
	 * After user confirmation, will delete a given global from the database.
	 * Removes it from our list of globals to display.
	 * @param globalToDelete Global to delete
	 */
	async deleteGlobal(globalToDelete: Variable) {
		await this.utils.confirm(`Are you sure you want to delete <b>${ globalToDelete.name }</b>?`);
		this.globalsService
			.deleteGlobal(globalToDelete)
			.then(() => this.toastrService.success(`Deleted <b>${ globalToDelete.name }</b>`))
			.catch(e => this.toastrService.error(`Error deleting <b>${ e.message }</b>`));
	}

	/**
	 * Opens a modal to add a new workflow to a given playbook or under a new playbook.
	 */
	editDescription() {
		const modalRef = this.modalService.open(MetadataModalComponent);
		modalRef.componentInstance.existing = true;
		modalRef.componentInstance.workflow = this.loadedWorkflow.clone();
		modalRef.result.then(workflow => this.loadedWorkflow = workflow).catch(() => null)
		return false;
	}

	closeActionSettingMenu() {
		this.cy.$('this.selectedAction.id').unselect();
		this.triggerCanvasResize();
	}

	triggerCanvasResize() {
		// const options = { zoom: this.cy.zoom(), pan: this.cy.pan() }
		// setTimeout(() => this.setupGraph(options), 255);
		let height, width;
		timer(0, 50).takeWhile(_ => height != this.cyRef.nativeElement.offsetHeight || width != this.cyRef.nativeElement.offsetWidth)
		.do(_ => {
			height = this.cyRef.nativeElement.offsetHeight
			width = this.cyRef.nativeElement.offsetWidth
		})
		.last()
		.subscribe(_ => window.dispatchEvent(new Event('resize')))	
	}
}
