import { Component, ViewEncapsulation, ViewChild, ElementRef, ChangeDetectorRef, OnInit,
	AfterViewChecked, OnDestroy} from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { DatatableComponent } from '@swimlane/ngx-datatable';
import { UUID } from 'angular2-uuid';
import { Observable } from 'rxjs';
import 'rxjs/Rx';
import { saveAs } from 'file-saver';
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
import { ExecutionService } from '../execution/execution.service';
import { SettingsService } from '../settings/settings.service';

import { AppApi } from '../models/api/appApi';
import { ActionApi, ActionType } from '../models/api/actionApi';
import { ParameterApi } from '../models/api/parameterApi';
import { ConditionApi } from '../models/api/conditionApi';
import { TransformApi } from '../models/api/transformApi';
import { DeviceApi } from '../models/api/deviceApi';
import { ReturnApi } from '../models/api/returnApi';
import { Playbook } from '../models/playbook/playbook';
import { Workflow } from '../models/playbook/workflow';
import { Action } from '../models/playbook/action';
import { Branch } from '../models/playbook/branch';
import { GraphPosition } from '../models/playbook/graphPosition';
import { Global } from '../models/global';
import { Argument, Variant } from '../models/playbook/argument';
import { User } from '../models/user';
import { Role } from '../models/role';
import { NodeStatus, NodeStatuses } from '../models/execution/nodeStatus';
import { ConditionalExpression } from '../models/playbook/conditionalExpression';
import { NodeStatusEvent } from '../models/execution/nodeStatusEvent';
import { ConsoleLog } from '../models/execution/consoleLog';
import { EnvironmentVariable } from '../models/playbook/environmentVariable';
import { PlaybookEnvironmentVariableModalComponent } from './playbook.environment.variable.modal.component';
import { WorkflowStatus } from '../models/execution/workflowStatus';
import { CodemirrorComponent } from '@ctrl/ngx-codemirror';
import { ActivatedRoute } from '@angular/router';
import { Variable } from '../models/variable';
import { MetadataModalComponent } from './metadata.modal.component';
import { Condition } from '../models/playbook/condition';

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
	@ViewChild('cyRef') cyRef: ElementRef;
	@ViewChild('workflowResultsTable') workflowResultsTable: DatatableComponent;
	@ViewChild('consoleContainer') consoleContainer: ElementRef;
	@ViewChild('consoleTable') consoleTable: DatatableComponent;
	@ViewChild('errorLogTable') errorLogTable: DatatableComponent;
	@ViewChild('environmentVariableTable') environmentVariableTable: DatatableComponent;
	@ViewChild('importFile') importFile: ElementRef;
	@ViewChild('accordion') apps_actions: ElementRef;
	@ViewChild('consoleArea') consoleArea: CodemirrorComponent;

	globals: Variable[] = [];
	relevantGlobals: Variable[] = [];
	users: User[];
	roles: Role[];

	//loadedPlaybook: Playbook;
	loadedWorkflow: Workflow;
	playbooks: Playbook[] = [];
	workflows: Workflow[] = [];
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
	nodeStatusStartedRelativeTimes: { [key: string]: string } = {};
	nodeStatusCompletedRelativeTimes: { [key: string]: string } = {};
	eventSource: any;
	consoleEventSource: any;
	playbookToImport: File;
	recalculateConsoleTableCallback: any;
	actionFilter: string = '';
	actionFilterControl = new FormControl();
	actionTypes = ActionType;

	tags: string[] = [];
	
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

	constructor(
		private playbookService: PlaybookService, private authService: AuthService,
		private toastrService: ToastrService, private activeRoute: ActivatedRoute,
		private cdr: ChangeDetectorRef, private utils: UtilitiesService,
		private modalService: NgbModal, private router: Router
	) {}

	/**
	 * On component initialization, we grab arrays of globals, app apis, and playbooks/workflows (id, name pairs).
	 * We also initialize an EventSoruce for Action Statuses for the execution results table.
	 * Also initialize cytoscape event bindings.
	 */
	ngOnInit(): void {

		const cyDummy = cytoscape();
		if (!cyDummy.clipboard) { clipboard(cytoscape, $); }
		if (!cyDummy.edgehandles) { cytoscape.use(edgehandles); }
		if (!cyDummy.gridGuide) { cytoscape.use(gridGuide); }
		if (!cyDummy.panzoom) { cytoscape.use(panzoom); }
		if (!cyDummy.undoRedo) { cytoscape.use(undoRedo); }

		this.playbookService.getGlobals().then(globals => this.globals = globals);
		this.playbookService.getApis().then(appApis => this.appApis = appApis.sort((a, b) => a.name > b.name ? 1 : -1));
		this.getPlaybooksWithWorkflows();
		this._addCytoscapeEventBindings();

		Observable.interval(30000).subscribe(() => {
			this.recalculateRelativeTimes();
		});

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
	 * Closes our SSEs on component destroy.
	 */
	ngOnDestroy(): void {
		if (this.eventSource && this.eventSource.close) { this.eventSource.close(); }
		if (this.consoleEventSource && this.consoleEventSource.close) { this.consoleEventSource.close(); }
	}

	changed(data: {value: string[]}) {
		this.tags = data.value;
	}

    ///------------------------------------------------------------------------------------------------------
	/// Console functions
	///------------------------------------------------------------------------------------------------------
	/**
	 * Sets up the EventStream for receiving console logs from the server. Binds various events to the event handler.
	 * Will currently return ALL stream actions and not just the ones manually executed.
	 */
	getConsoleSSE(workflowExecutionId: string) {
		if (this.consoleEventSource) this.consoleEventSource.close();

		return this.authService.getEventSource(`/api/streams/console/log?workflow_execution_id=${ workflowExecutionId }`)
			.then(eventSource => {
				this.consoleEventSource = eventSource;
				this.consoleEventSource.onerror = (e: any) => this.statusEventErrorHandler(e);
				this.consoleEventSource.addEventListener('log', (e: any) => this.consoleEventHandler(e));
			});
	}

    consoleEventHandler(message: any): void {
		console.log('c', message)
		const consoleEvent = plainToClass(ConsoleLog, (JSON.parse(message.data) as object));
		const newConsoleLog = consoleEvent.toNewConsoleLog();

		// Induce change detection by slicing array
		this.consoleLog.push(newConsoleLog);
		this.consoleLog = this.consoleLog.slice();
	}

	get consoleContent() {
		let content = `******************************* Console Output *******************************`;
		this.consoleLog.forEach(log => {
			content += '\n' + log.message;
		})
		return content;
	}

	///------------------------------------------------------------------------------------------------------
	/// Playbook CRUD etc functions
	///------------------------------------------------------------------------------------------------------
	/**
	 * Sets up the EventStream for receiving stream actions from the server. Binds various events to the event handler.
	 * Will currently return ALL stream actions and not just the ones manually executed.
	 */
	getNodeStatusSSE(workflowExecutionId: string) {
		if (this.eventSource) this.eventSource.close();

		return this.authService.getEventSource(`/api/streams/workflowqueue/actions?workflow_execution_id=${ workflowExecutionId }`)
			.then(eventSource => {
				this.eventSource = eventSource
				this.eventSource.onerror = (e: any) => this.statusEventErrorHandler(e);

				Object.values(NodeStatuses)
					  .forEach(status => this.eventSource.addEventListener(status, (e: any) => this.nodeStatusEventHandler(e)));
			});
	}

	/**
	 * For an incoming action, will try to find the matching action in the graph (if applicable).
	 * Will style nodes based on the action status (executing/success/failure).
	 * Will update the information in the action statuses table as well, adding new rows or updating existing ones.
	 */
	nodeStatusEventHandler(message: any): void {
		const nodeStatusEvent = plainToClass(NodeStatusEvent, (JSON.parse(message.data) as object));
		console.log('action', nodeStatusEvent);

		// If we have a graph loaded, find the matching node for this event and style it appropriately if possible.
		if (this.cy) {
			const matchingNode = this.cy.elements(`node[_id="${ nodeStatusEvent.node_id }"]`);
			const nodeType = matchingNode.data('type');
			const incomingEdges = matchingNode.incomers('edge');
			const outgoingEdges = matchingNode.outgoers('edge');

			if (matchingNode) {
				switch (nodeStatusEvent.status) {
					case NodeStatuses.EXECUTING:
						matchingNode.removeClass('success-highlight');
						matchingNode.removeClass('failure-highlight');
						matchingNode.addClass('executing-highlight');
						matchingNode.removeClass('awaiting-data-highlight');
						incomingEdges.addClass('success-highlight');	
						break;
					case NodeStatuses.SUCCESS:
						matchingNode.addClass('success-highlight');
						matchingNode.removeClass('failure-highlight');
						matchingNode.removeClass('executing-highlight');
						matchingNode.removeClass('awaiting-data-highlight');
						//incomingEdges.addClass('success-highlight');
						//incomingEdges.removeClass('executing-highlight');
						if (nodeType != ActionType.CONDITION) {
							outgoingEdges.addClass('success-highlight');
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
									   .find(as => as.execution_id === nodeStatusEvent.execution_id && as.node_id == nodeStatusEvent.node_id);
		if (matchingNodeStatus) {
			matchingNodeStatus.status = nodeStatusEvent.status;

			switch (message.type) {
				case NodeStatuses.EXECUTING:
					// shouldn't happen
					matchingNodeStatus.started_at = nodeStatusEvent.started_at;
					break;
				case NodeStatuses.SUCCESS:
				case NodeStatuses.FAILURE:
					matchingNodeStatus.completed_at = nodeStatusEvent.completed_at;
					matchingNodeStatus.result = nodeStatusEvent.result;
					break;
				case NodeStatuses.AWAITING_DATA:
					// don't think anything needs to happen here
					break;
				default:
					this.toastrService.warning(`Unknown Action Status SSE Type: ${message.type}.`);
					break;
			}

			this.recalculateRelativeTimes(matchingNodeStatus);
			this.calculateLocalizedTimes(matchingNodeStatus);
		} else {
			const newNodeStatus = nodeStatusEvent.toNewNodeStatus();
			this.calculateLocalizedTimes(newNodeStatus);
			this.nodeStatuses.push(newNodeStatus);
		}
		// Induce change detection by slicing array
		this.nodeStatuses = this.nodeStatuses.slice();
	}

	statusEventErrorHandler(e: any) {
		if (this.eventSource && this.eventSource.close)
			this.eventSource.close();
		if (this.consoleEventSource && this.consoleEventSource.close)
			this.consoleEventSource.close();

		const options = {backdrop: undefined, closeButton: false, buttons: { ok: { label: 'Reload Page' }}}
		this.utils
			.alert('The server stopped responding. Reload the page to try again.', options)
			.then(() => location.reload(true))
	}

	/**
	 * Executes the loaded workflow as it exists on the server. Will not currently execute the workflow as it stands.
	 */
	executeWorkflow(): void {
		if (!this.loadedWorkflow) { return; }
		this.clearExecutionHighlighting();

		const executionId = UUID.UUID();
		Promise.all([
			this.getNodeStatusSSE(executionId),
			// this.getConsoleSSE(executionId)
		]).then(() => {
			this.playbookService.addWorkflowToQueue(this.loadedWorkflow.id, executionId)
				.then((workflowStatus: WorkflowStatus) => {
					this.toastrService.success(`Starting <b>${this.loadedWorkflow.name}</b>`)
				})
				.catch(e => this.toastrService.error(`Error starting execution of ${this.loadedWorkflow.name}: ${e.message}`));
		})
	}

	/**
	 * Loads a workflow from a given playbook / workflow name pair and calls function to set up graph.
	 * @param playbook Playbook to load
	 * @param workflow Workflow to load
	 */
	loadWorkflow(workflow: Workflow): void {
		this.closeWorkflow();

		if (workflow.id) {
			this.playbookService.loadWorkflow(workflow.id)
				.then(loadedWorkflow => {
					this.loadedWorkflow = loadedWorkflow;
					this.setupGraph();
				})
				.catch(e => this.toastrService.error(`Error loading workflow "${workflow.name}": ${e.message}`));
		} else {
			this.loadedWorkflow = workflow;
			this.setupGraph();
		}
	}

	returnToWorkflows() {
		this.utils.confirm('Are you sure you? Any unsaved changes will be lost!').then(() => {
			this.router.navigateByUrl(`/workflows`);
		})
		return false;
	}

	routeToWorkflow(workflow: Workflow): void {
		this.router.navigateByUrl(`/workflows/${ workflow.id }`);
	}

	setupGraph(): void {
		// Convert our selection arrays to a string
		if (!this.loadedWorkflow.actions) { this.loadedWorkflow.actions = []; }

		// Refresh the console log so that it displays correctly after being hidden
		setTimeout(() => {
			if (this.consoleArea && this.consoleArea.codeMirror) this.consoleArea.codeMirror.refresh();
		});

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
						'width': 'label',
						'height': 'label',
						'padding': '10px'
					},
				},
				{
					selector: `node[type="${ ActionType.ACTION }"]`,
					css: {
						'background-color': '#bbb',
					},
				},
				{
					selector: `node[type="${ ActionType.CONDITION }"]`,
					css: {
						'shape': 'diamond',
						'padding': '30px'
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
					selector: 'edge.executing-highlight',
					css: {
						'width': '5px',
						'target-arrow-color': '#ffef47',
						'line-color': '#ffef47',
						'transition-property': 'line-color, width',
						'transition-duration': '0.25s',
					},
				},
				{
					selector: 'edge.success-highlight',
					css: {
						'width': '5px',
						'target-arrow-color': '#399645',
						'line-color': '#399645',
						'transition-property': 'line-color, width',
						'transition-duration': '0.5s',
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
		});

		// Enable various Cytoscape extensions
		// Undo/Redo extension
		this.ur = this.cy.undoRedo({});

		this.ur.action('add-walkoff-node', (args) => {
			args.addedNode = this.insertNode(args);
			return args;
		}, (args) => {
			this.cy.elements(`[_id="${ args.addedNode.data._id }"]`).remove();
			return args;
		})

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
					const sourceActionApi = this._getAction(sourceAction.app_name, sourceAction.app_version, sourceAction.action_name);

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
					newBranch.status = defaultStatus;
					newBranch.priority = 1;

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

		// Load the data into the graph
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

		const actions = this.loadedWorkflow.actions.map(action => {
			const node: any = { group: 'nodes', position: this.utils.cloneDeep(action.position) };
			node.data = {
				id: action.id,
				_id: action.id,
				label: action.name,
				isStartNode: action.id === this.loadedWorkflow.start,
				hasErrors: action.has_errors,
				type: ActionType.ACTION
			};
			return node;
		});

		const conditionals = this.loadedWorkflow.conditions.map(condition => {
			const node: any = { group: 'nodes', position: this.utils.cloneDeep(condition.position) };
			node.data = {
				id: condition.id,
				_id: condition.id,
				label: condition.name,
				isStartNode: condition.id === this.loadedWorkflow.start,
				hasErrors: condition.has_errors,
				type: ActionType.CONDITION
			};
			return node;
		});

		this.cy.add([].concat(edges, actions, conditionals));

		this.cy.fit(null, 50);

		this.setStartNode(this.loadedWorkflow.start);

		// Note: these bindings need to use arrow notation
		// to actually be able to use 'this' to refer to the PlaybookComponent.
		// Configure handler when user clicks on node or edge
		this.cy.on('select', 'node', (e: any) => this.onNodeSelect(e));
		this.cy.on('select', 'edge', (e: any) => this.onEdgeSelect(e));
		this.cy.on('unselect', (e: any) => this.onUnselect(e));

		// Configure handlers when nodes/edges are added or removed
		this.cy.on('add', 'node', (e: any) => this.onNodeAdded(e));
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

	/**
	 * Closes the active workflow and clears all relevant variables.
	 */
	closeWorkflow(): void {
		// this.loadedPlaybook = null;
		this.loadedWorkflow = null;
		this.selectedBranchParams = null;
		this.selectedAction = null;
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
		workflowToSave.actions.forEach(action => {
			// Set action name if empty
			if (!action.name) action.name = workflowToSave.getNextActionName(action.action_name);

			// Set the new cytoscape positions on our loadedworkflow
			action.position = cyData.find(cyAction => cyAction.data._id === action.id).position;

			// Properly sanitize arguments through the tree
			if (action.arguments) this._sanitizeArgumentsForSave(action, workflowToSave);

			// if (action.trigger) this._sanitizeExpressionAndChildren(action.trigger);
		});

		workflowToSave.conditions.forEach(condition => {
			// Set action name if empty
			if (!condition.name) condition.name = workflowToSave.getNextActionName(condition.action_name, ActionType.CONDITION);

			// Set the new cytoscape positions on our loadedworkflow
			condition.position = cyData.find(cyAction => cyAction.data._id === condition.id).position;

			// Properly sanitize arguments through the tree
			if (condition.arguments) this._sanitizeArgumentsForSave(condition, workflowToSave);

			// if (condition.trigger) this._sanitizeExpressionAndChildren(condition.trigger);
		});

		workflowToSave.branches.forEach(branch => {
			this._sanitizeExpressionAndChildren(branch.condition);
		});

		if (this.loadedWorkflow.id) {
			this.playbookService.saveWorkflow(workflowToSave).then(savedWorkflow => {
				this.loadedWorkflow = savedWorkflow;
				this.setupGraph();
				this.toastrService.success(`Saved <b>${ savedWorkflow.name }</b>`);
			}).catch(e => this.toastrService.error(`Error saving workflow ${workflowToSave.name}: ${e.message}`));
		} else {
			this.playbookService.newWorkflow(workflowToSave).then(savedWorkflow => {
				//this.loadedWorkflow = savedWorkflow;
				//this.setupGraph()
				this.toastrService.success(`Saved <b>${ savedWorkflow.name }</b>`);
				this.router.navigateByUrl(`/workflows/${ savedWorkflow.id }`);
			}).catch(e => this.toastrService.error(`Error saving workflow ${workflowToSave.name}: ${e.message}`));
		}
	}

	/**
	 * Gets a list of all the loaded playbooks along with their workflows.
	 */
	getPlaybooksWithWorkflows(): void {
		this.playbookService.getWorkflows()
			.then(workflows => {
				this.workflows = workflows;
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
			});
	}

	_sanitizeExpressionAndChildren(expression: ConditionalExpression): void {
		if (!expression) { return; }

		if (expression.conditions && expression.conditions.length) {
			expression.conditions.forEach(condition => {
				//this._sanitizeArgumentsForSave(condition.arguments);

				// condition.transforms.forEach(transform => {
				// 	this._sanitizeArgumentsForSave(transform.arguments);
				// });
			});
		}

		if (expression.child_expressions && expression.child_expressions.length) {
			expression.child_expressions.forEach(childExpr => {
				childExpr.conditions.forEach(condition => {
					//this._sanitizeArgumentsForSave(condition.arguments);

					// condition.transforms.forEach(transform => {
					// 	this._sanitizeArgumentsForSave(transform.arguments);
					// });
				});

				this._sanitizeExpressionAndChildren(childExpr);
			});
		}
	}

	/**
	 * Sanitizes an argument so we don't have bad data on save, such as a value when reference is specified.
	 * @param argument The argument to sanitize
	 */
	_sanitizeArgumentsForSave(action: Action | Condition, workflow: Workflow): void {
		const args = action.arguments;

		console.log('hhhjhh', action.arguments)

		// Filter out any arguments that are blank, essentially
		const idsToRemove: number[] = [];
		for (const argument of args) {
			// First trim any string inputs for sanitation and so we can check against ''
			if (typeof (argument.value) === 'string') { argument.value = argument.value.trim(); }

			// If value and reference are blank, add this argument's ID in the array to the list
			// Add them in reverse so we don't have problems with the IDs sliding around on the splice
			if (!argument.value) {
				idsToRemove.unshift(args.indexOf(argument));
			}

			// Make sure reference is valid for this action
			if (argument.variant == Variant.ACTION_RESULT) {	
				const validReferences = [].concat(
					workflow.getPreviousActions(action).map(a => a.id),
					this.globals.map(g => g.id),
					workflow.environment_variables.map(v => v.id)
				)
				console.log(validReferences)
				if (!validReferences.includes(argument.value)) {
					console.log('hi')
					idsToRemove.unshift(args.indexOf(argument));
				}
			}
		}
		// Actually splice out all the args
		for (const id of idsToRemove) {
			args.splice(id, 1);
		}
	}

	/**
	 * Specifies a new conditional expression for a given action.
	 * @param action Action to specify the trigger for
	 */
	// specifyTrigger(action: Action): void {
	// 	if (action.trigger) { return; }
	// 	action.trigger = new ConditionalExpression();
	// }

	/**
	 * Deletes the conditional expression for a given action.
	 * @param action Action to remove the trigger for
	 */
	// removeTrigger(action: Action): void {
	// 	delete action.trigger;
	// }

	/**
	 * Specifies a new conditional expression for a given action.
	 * @param branch Branch to specify the trigger for
	 */
	specifyCondition(branch: Branch): void {
		if (branch.condition) { return; }
		branch.condition = new ConditionalExpression();
	}

	/**
	 * Specifies a new conditional expression for a given branch.
	 * @param branch Branch to specify the trigger for
	 */
	removeCondition(branch: Branch): void {
		delete branch.condition;
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
		const actionApi = this._getAction(action.app_name, action.app_version, action.action_name);

		const queryPromises: Array<Promise<any>> = [];

		if (!this.users &&
			(actionApi.parameters.findIndex(p => p.schema.type === 'user') > -1 ||
			actionApi.parameters.findIndex(p => p.schema.items && p.schema.items.type === 'user') > -1)) {
			this.waitingOnData = true;
			queryPromises.push(this.playbookService.getUsers().then(users => this.users = users));
		}
		if (!this.roles &&
			(actionApi.parameters.findIndex(p => p.schema.type === 'role') > -1 ||
			actionApi.parameters.findIndex(p => p.schema.items && p.schema.items.type === 'role') > -1)) {
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
			returnTypes: this._getAction(sourceAction.app_name, sourceAction.app_version, sourceAction.action_name).returns,
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
	 * This function fires when a node is removed. If the node was the start node, it sets it to a new root node.
	 * It also removes the corresponding action from the workflow.
	 * @param e JS Event fired
	 */
	onNodeRemoved(event: any): void {
		const node = event.target;
		const data = node.data();

		// If the start node was deleted, set it to one of the roots of the graph
		if (data && node.isNode() && this.loadedWorkflow.start === data._id) { this.setStartNode(null); }
		if (this.selectedAction && this.selectedAction.id === data._id) { this.selectedAction = null; }

		// Delete the action from the workflow and delete any branches that reference this action
		this.loadedWorkflow.actions = this.loadedWorkflow.actions.filter(a => a.id !== data._id);
		this.loadedWorkflow.conditions = this.loadedWorkflow.conditions.filter(a => a.id !== data._id);
		this.loadedWorkflow.branches = this.loadedWorkflow.branches
			.filter(ns => !(ns.source_id === data._id || ns.destination_id === data._id));
	}

	/**
	 * This function fires when an action is dropped onto the graph and fires the insertNode function.
	 * @param e JS Event fired
	 */
	handleDropEvent(e: any): void {
		if (this.cy === null) { return; }

		const appName: string = e.dragData.appName;
		const actionApi: ActionApi = e.dragData.actionApi;

		// The following coordinates is where the user dropped relative to the
		// top-left of the graph
		const dropPosition: GraphPosition = plainToClass(GraphPosition, {
			x: e.mouseEvent.layerX,
			y: e.mouseEvent.layerY,
		});

		this.ur.do('add-walkoff-node', {
			appName: appName,
			appVersion: actionApi.app_version,
			actionName: actionApi.name,
			location: dropPosition,
			shouldUseRenderedPosition: true
		})
	}

	/**
	 * This function is fired when an action on the left-hand list is double clicked.
	 * It drops a new node of that action in the center of the visible graph.
	 * @param appName App name the action resides under
	 * @param actionName Name of the action that was double clicked
	 */
	handleDoubleClickEvent(actionApi: ActionApi): void {
		if (this.cy === null) { return; }

		const extent = this.cy.extent();

		const centerGraphPosition = plainToClass(GraphPosition, { x: this.avg(extent.x1, extent.x2), y: this.avg(extent.y1, extent.y2) });

		this.ur.do('add-walkoff-node', {
			appName: actionApi.app_name,
			appVersion: actionApi.app_version,
			actionName: actionApi.name,
			location: centerGraphPosition,
			shouldUseRenderedPosition: false
		})
	}

	/**
	 * Simple average function to get the avg. of 2 numbers.
	 * @param a 1st number
	 * @param b 2nd number
	 */
	avg(a: number, b: number): number {
		return (a + b) / 2;
	}

	/**
	 * Inserts node into the graph and adds a corresponding action to the loadedworkflow.
	 * @param appName App name the action resides under
	 * @param actionName Name of the action to add
	 * @param location Graph Position, where to create the node
	 * @param shouldUseRenderedPosition Whether or not to use rendered or "real" graph position
	 */
	insertNode({appName, appVersion, actionName, location, shouldUseRenderedPosition, firstTime, addedNode}) {
		// Grab a new ID for both the ID of the node and the ID of the action in the workflow
		const newActionUuid = (firstTime) ? UUID.UUID() : addedNode.data._id;

		const args: Argument[] = [];
		const parameters = this._getAction(appName, appVersion, actionName).parameters;
		// TODO: might be able to remove this entirely
		// due to the argument component auto-initializing default values
		if (parameters && parameters.length) {
			this._getAction(appName, appVersion, actionName).parameters.forEach((parameter) => {
				args.push(this.getDefaultArgument(parameter));
			});
		}

		const actionType = this._getAction(appName, appVersion, actionName).node_type;
		const uniqueActionName = this.loadedWorkflow.getNextActionName(actionName, actionType);

		switch(actionType) {
			case ActionType.CONDITION:
				this.insertConditional(appName, actionName, newActionUuid, uniqueActionName, appVersion, args)
				break;
			default: 
				this.insertAction(appName, actionName, newActionUuid, uniqueActionName, appVersion, args);
		}

		// Add the node with the new ID to the graph in the location dropped into by the mouse.
		const nodeToBeAdded = {
			group: 'nodes',
			data: {
				id: newActionUuid,
				_id: newActionUuid,
				label: uniqueActionName,
				type: actionType
			},
			renderedPosition: null as GraphPosition,
			position: null as GraphPosition,
		};

		if (shouldUseRenderedPosition) {
			nodeToBeAdded.renderedPosition = location;
		} else { nodeToBeAdded.position = location; }

		//this.ur.do('add', nodeToBeAdded);
		this.cy.add(nodeToBeAdded);

		return nodeToBeAdded;
	}

	private insertAction(appName: any, actionName: any, newActionUuid: any, uniqueActionName: string, appVersion: any, args: Argument[]) {
		const actionToBeAdded = new Action();
		actionToBeAdded.id = newActionUuid;
		actionToBeAdded.name = uniqueActionName;
		actionToBeAdded.app_name = appName;
		actionToBeAdded.app_version = appVersion;
		actionToBeAdded.action_name = actionName;
		actionToBeAdded.arguments = args;
		this.loadedWorkflow.actions.push(actionToBeAdded);
	}

	private insertConditional(appName: any, actionName: any, newActionUuid: any, uniqueActionName: string, appVersion: any, args: Argument[]) {
		const condition = new Condition();
		condition.id = newActionUuid;
		condition.name = uniqueActionName;
		condition.app_name = appName;
		condition.app_version = appVersion;
		condition.action_name = actionName;
		condition.arguments = args;
		this.loadedWorkflow.conditions.push(condition);
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
			this.loadedWorkflow.actions.push(pastedAction);

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
	}

	/**
	 * Clears the red/green highlighting in the cytoscape graph.
	 */
	clearExecutionHighlighting(): void {
		this.cy.elements().removeClass('success-highlight failure-highlight executing-highlight');
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

	/**
	 * Removes all selected nodes and edges.
	 */
	removeSelectedNodes(): void {
		const selecteds = this.cy.$(':selected');
		// Unselect the elements first to remove the parameters editor if need be
		// Because deleting elements doesn't unselect them for some reason
		this.cy.elements(':selected').unselect();
		if (selecteds.length > 0) { this.ur.do('remove', selecteds); }
	}

	/**
	 * Adds keyboard event bindings for cut/copy/paste/etc.
	 */
	_addCytoscapeEventBindings(): void {
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

	///------------------------------------------------------------------------------------------------------
	/// Utility functions
	///------------------------------------------------------------------------------------------------------
	// /**
	//  * Gets a list of playbook names from our list of playbooks.
	//  */
	// getPlaybooks(): string[] {
	// 	return this.playbooks.map(pb => pb.name);
	// }

	/**
	 * Gets an ActionApi object by app and action name
	 * @param appName App name the action resides under
	 * @param actionName Name of the ActionApi to query
	 */
	_getAction(appName: string, appVersion: string, actionName: string): ActionApi {
		return this.appApis.find(a => a.name === appName).action_apis.find(a => a.name === actionName);
		return this.appApis.find(a => a.name === appName && a.app_version == appVersion)
				.action_apis.find(a => a.name === actionName);
	}

	/**
	 * Gets a given argument matching an inputted parameter API.
	 * Adds a new argument to the selected action with default values if the argument doesn't exist.
	 * @param parameterApi Parameter API object relating to the argument to return
	 */
	getOrInitializeSelectedActionArgument(parameterApi: ParameterApi): Argument {
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
		if (parameterApi.schema.type === 'array') { 
			initialValue = [];
		} else if (parameterApi.schema.type === 'object') {
			initialValue = {};
		} else if (parameterApi.schema.type === 'boolean') {
			initialValue = false;
		}

		return plainToClass(Argument, {
			name: parameterApi.name,
			variant: Variant.STATIC_VALUE,
			value: (parameterApi.schema.default) ? parameterApi.schema.default : initialValue,
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
		return this._getAction(appName, appVersion, actionName).parameters.find(a => a.name === inputName);
	}

	/**
	 * Filters only the apps that have actions specified
	 */
	getAppsWithActions(): AppApi[] {
		return this.appApis.filter(a => a.action_apis && a.getFilteredActionApis(this.actionFilter).length);
	}

	/**
	 * Converts an input object/value to a friendly string for display in the workflow status table.
	 * @param input Input object / value to convert
	 */
	getFriendlyJSON(input: any): string {
		if (!input) { return 'N/A'; }
		let out = JSON.stringify(input, null, 1);
		out = out.replace(/[\{\[\}\]"]/g, '').trim();
		if (!out) { return 'N/A'; }
		return out;
	}

	/**
	 * Converts an input argument array to a friendly string for display in the workflow status table.
	 * @param args Array of arguments to convert
	 */
	getFriendlyArguments(args: Argument[]): string {
		if (!args || !args.length) { return 'N/A'; }

		const obj: { [key: string]: string } = {};
		args.forEach(element => {
			if (element.value) { obj[element.name] = element.value; }
		});

		let out = JSON.stringify(obj, null, 1);
		out = out.replace(/[\{\}"]/g, '');
		return out;
	}

	/**
	 * Removes the white space in a given string.
	 * @param input Input string to remove the whitespace of
	 */
	removeWhitespace(input: string): string {
		return input.replace(/\s/g, '');
	}

	/**
	 * Recalculates the relative times shown for start/end date timestamps (e.g. '5 hours ago').
	 */
	recalculateRelativeTimes(specificStatus?: NodeStatus): void {
		let targetStatuses: NodeStatus[];
		if (specificStatus) {
			targetStatuses = [specificStatus];
		} else {
			targetStatuses = this.nodeStatuses;
		}
		if (!targetStatuses || !targetStatuses.length ) { return; }

		targetStatuses.forEach(nodeStatus => {
			if (nodeStatus.started_at) {
				this.nodeStatusStartedRelativeTimes[nodeStatus.execution_id] =
					this.utils.getRelativeLocalTime(nodeStatus.started_at);
			}
			if (nodeStatus.completed_at) {
				this.nodeStatusCompletedRelativeTimes[nodeStatus.execution_id] =
					this.utils.getRelativeLocalTime(nodeStatus.completed_at);
			}
		});
	}

	/**
	 * Adds/updates localized time strings to a status object.
	 * @param status Action Status to mutate
	 */
	calculateLocalizedTimes(status: NodeStatus): void {
		if (status.started_at) {
			status.localized_started_at = this.utils.getLocalTime(status.started_at);
		}
		if (status.completed_at) {
			status.localized_completed_at = this.utils.getLocalTime(status.completed_at);
		}
	}

	/**
	 * Returns errors in the loaded workflow
	 */
	getErrors() : any[] {
		if (!this.loadedWorkflow) return [];
		return this.loadedWorkflow.all_errors.map(error => ({ error }));
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
			console.log(this.loadedWorkflow.environment_variables, variable)
			if (!this.loadedWorkflow.environment_variables) this.loadedWorkflow.environment_variables = [];
			this.loadedWorkflow.environment_variables.push(variable);
			this.loadedWorkflow.environment_variables = this.loadedWorkflow.environment_variables.slice();
			argument.value = variable.id;
		}).catch(() => argument.value = '')
	}

	workflowVariablesModal() {
		const modalRef = this.modalService.open(PlaybookEnvironmentVariableModalComponent);
		modalRef.result.then(variable => {
			console.log(this.loadedWorkflow.environment_variables, variable)
			if (!this.loadedWorkflow.environment_variables) this.loadedWorkflow.environment_variables = [];
			this.loadedWorkflow.environment_variables.push(variable);
			this.loadedWorkflow.environment_variables = this.loadedWorkflow.environment_variables.slice();
		}).catch(() => null)
	}

	/**
	 * Opens a modal to add a new workflow to a given playbook or under a new playbook.
	 */
	editDescription() {
		const modalRef = this.modalService.open(MetadataModalComponent);
		modalRef.componentInstance.existing = true;
		modalRef.componentInstance.currentTags = this.currentTags;
		modalRef.componentInstance.existingWorkflows = this.workflows;
		modalRef.componentInstance.workflow = this.loadedWorkflow.clone();
		modalRef.result.then(workflow => this.loadedWorkflow = workflow).catch(() => null)
		return false;
	}

	get currentTags(): string[] {
		let tags = this.loadedWorkflow.tags || [];
		this.workflows.forEach(w => tags = tags.concat(w.tags));
		return tags.filter((v, i, a) => a.indexOf(v) == i);
	}
}
