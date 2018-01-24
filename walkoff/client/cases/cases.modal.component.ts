import { Component, Input, ViewEncapsulation } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import * as d3 from 'd3';
import { TreeLayout } from 'd3';
import { Selection, EnterElement } from 'd3-selection';

import { CasesService } from './cases.service';

import { Case } from '../models/case/case';
import { CaseNode } from '../models/case/caseNode';
import { AvailableSubscription } from '../models/case/availableSubscription';
import { Subscription } from '../models/case/subscription';

@Component({
	encapsulation: ViewEncapsulation.None,
	selector: 'case-modal',
	templateUrl: 'client/cases/cases.modal.html',
	styleUrls: [
		'client/cases/cases.modal.css',
	],
	providers: [CasesService],
})
export class CasesModalComponent {
	@Input() workingCase: Case;
	@Input() title: string;
	@Input() submitText: string;
	@Input() availableSubscriptions: AvailableSubscription[] = [];
	@Input() subscriptionTree: CaseNode;
	@Input() workingEvents: Array<{ name: string, isChecked: boolean }> = [];

	selectedNode: { name: string, id: number, type: string } = { name: '', id: 0, type: '' };
	treemap: TreeLayout<{}>;
	svg: Selection<Element | EnterElement | Document | Window, {}, HTMLElement, Window> ;
	root: any;
	i = 0;
	existingSubscriptions: Array<{ id: number, type: string }>;

	constructor(
		private casesService: CasesService, private activeModal: NgbActiveModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig) {}

	ngOnInit(): void {
		this.toastyConfig.theme = 'bootstrap';
		this.existingSubscriptions = this.workingCase.subscriptions.map(s => {
			return { id: s.id, type: s.type };
		});

		// Set the dimensions and margins of the diagram
		const margin = { top: 20, right: 90, bottom: 30, left: 90 };
		const width = 1350 - margin.left - margin.right;
		const height = 500 - margin.top - margin.bottom;

		// appends a 'group' element to 'svg'
		// moves the 'group' element to the top left margin
		this.svg = d3.select('svg#caseSubscriptionsTree')
			.attr('width', width + margin.right + margin.left)
			.attr('height', height + margin.top + margin.bottom)
			.append('g')
			.attr('transform', `translate(${margin.left},${margin.top})`);

		// declares a tree layout and assigns the size
		this.treemap = d3.tree().size([height, width]);

		// Assigns parent, children, height, depth
		this.root = d3.hierarchy(this.subscriptionTree);
		this.root.x0 = height / 2;
		this.root.y0 = 0;

		//Mark our controller as included if necessary
		if (this.existingSubscriptions.find(s => s.type === 'controller')) { this.root.data._included = true; }

		// Check for collapse after the second level
		if (this.root.children && this.root.children.length) {
			this.root.children.forEach(this.checkInclusionAndCheckChildrenForExpansion);
		}

		this.update(this.root);
	}

	update(source: any): void {
		const self = this;
		const duration = 400;
		// Assigns the x and y position for the nodes
		const treeData = this.treemap(self.root);

		// Compute the new tree layout.
		const nodes = treeData.descendants();
		const links = treeData.descendants().slice(1);

		// Normalize for fixed-depth.
		nodes.forEach(d => d.y = d.depth * 180);

		// ****************** Nodes section ***************************
		// Update the nodes...
		const node = self.svg.selectAll('g.node')
			.data(nodes, function (d: any) { return d.id || (d.id = ++self.i); });

		// Enter any new modes at the parent's previous position.
		const nodeEnter = node.enter().append('g')
			.classed('node', true)
			.classed('included', (d: any) => d.data._included)
			.attr('transform', d => `translate(${source.y0},${source.x0})`)
			.attr('id', (d: any) => self.getUid(d.data))
			.on('click', d => self.click(d, self))
			.on('dblclick', d => self.dblclick(d, self));

		// Add Circle for the nodes
		nodeEnter.append('circle')
			.classed('node', true)
			.attr('r', 1e-6)
			.style('fill', (d: any) => d._children ? 'lightsteelblue' : '#fff');

		// Add labels for the nodes
		nodeEnter.append('text')
			.attr('dy', '.35em')
			.attr('x', (d: any) => d.children || d._children ? -13 : 13)
			.attr('text-anchor', (d: any) => d.children || d._children ? 'end' : 'start')
			.text((d: any) => d.data.name);

		// UPDATE
		const nodeUpdate = nodeEnter.merge(node);

		// Transition to the proper position for the node
		nodeUpdate.transition()
			.duration(duration)
			.attr('transform', d => `translate(${d.y},${d.x})`);

		// Update the node attributes and style
		nodeUpdate.select('circle.node')
			.attr('r', 10)
			.style('fill', (d: any) => d._children ? 'lightsteelblue' : '#fff');

		// Remove any exiting nodes
		const nodeExit = node.exit().transition()
			.duration(duration)
			.attr('transform', d => `translate(${source.y},${source.x})`)
			.remove();

		// On exit reduce the node circles size to 0
		nodeExit.select('circle')
			.attr('r', 1e-6);

		// On exit reduce the opacity of text labels
		nodeExit.select('text')
			.style('fill-opacity', 1e-6);

		// ****************** links section ***************************

		// Update the links...
		const link = self.svg.selectAll('path.link')
			.data(links, (d: any) => d.id);

		// Enter any new links at the parent's previous position.
		const linkEnter = link.enter().insert('path', 'g')
			.classed('link', true)
			.attr('d', d => {
				const o = { x: source.x0, y: source.y0 };
				return self.diagonal(o, o);
			});

		// UPDATE
		const linkUpdate = linkEnter.merge(link);

		// Transition back to the parent element position
		linkUpdate.transition()
			.duration(duration)
			.attr('d', d => self.diagonal(d, d.parent));

		// Remove any exiting links
		link.exit().transition()
			.duration(duration)
			.attr('d', d => {
				const o = { x: source.x, y: source.y };
				return self.diagonal(o, o);
			})
			.remove();

		// Store the old positions for transition.
		nodes.forEach((d: any) => {
			d.x0 = d.x;
			d.y0 = d.y;
		});
	}

	/**
	 * This function recursively checks if each node should be included or expanded.
	 * @param d Node data
	 */
	checkInclusionAndCheckChildrenForExpansion(d: any): boolean {
		if (this.existingSubscriptions.find(s => s.id === d.data.id && s.type === d.data.type)) { d.data._included = true; }
		let expanded = false;

		if (d.children) {
			d.children.forEach(function (child: any) {
				expanded = this.checkInclusionAndCheckChildrenForExpansion(child) || expanded;
			});
		}

		if (!expanded && d.children) {
			d._children = d.children;
			d.children = null;
		}
		
		return d.data._included;
	}

	/**
	 * Creates a curved (diagonal) path from parent to the child nodes.
	 * @param s Source node
	 * @param d Destination node
	 */
	diagonal(s: any, d: any): string {
		return `M ${s.y} ${s.x}
			C ${(s.y + d.y) / 2} ${s.x},
			${(s.y + d.y) / 2} ${d.x},
			${d.y} ${d.x}`;
	}

	/**
	 * Selects our node on click.
	 * @param d Node data
	 * @param self This component reference
	 */
	click(d: any, self: CasesModalComponent): void {
		if (!d.data.type) { return; }

		self.selectedNode = { name: d.data.name, id: d.data.id, type: d.data.type };

		const availableEvents = self.availableSubscriptions.find(a => a.type === d.data.type).events;

		const subscription = self.workingCase.subscriptions.find(s => s.id === d.data.id && s.type === d.data.type);

		const subscriptionEvents = subscription ? subscription.events : [];

		self.workingEvents = [];

		availableEvents.forEach(function (event) {
			self.workingEvents.push({
				name: event,
				isChecked: subscriptionEvents.indexOf(event) > -1,
			});
		});

		//Clear highlighting on other highlighted node(s)
		d3.selectAll('g.node.highlighted')
			.classed('highlighted', false);

		//Highlight this node now.
		d3.select(`g.node#${this.getUid(self.selectedNode)}`)
			.classed('highlighted', true);
	}

	/**
	 * Toggle children on double click.
	 * @param d Node data
	 * @param self This component reference
	 */
	dblclick(d: any, self: CasesModalComponent): void {
		if (d.children) {
			d._children = d.children;
			d.children = null;
		} else {
			d.children = d._children;
			d._children = null;
		}
		self.update(d);
	}

	handleEventSelectionChange(event: any, isChecked: boolean): void {
		if (!this.selectedNode.name) {
			console.error('Attempted to select events without a node selected.');
			return;
		}

		event.isChecked = isChecked;

		let matchingSubscription = this.workingCase.subscriptions.find(s => s.id === this.selectedNode.id);

		//If no subscription is returned, it doesn't exist yet; add it.
		if (!matchingSubscription) {
			matchingSubscription = new Subscription();
			matchingSubscription.id = this.selectedNode.id;
			matchingSubscription.type = this.selectedNode.type;

			this.workingCase.subscriptions.push(matchingSubscription);

			//style the node in d3 as well
			d3.select('svg#caseSubscriptionsTree').select(`g.node#${this.getUid(this.selectedNode)}`)
				.classed('included', true)
				.datum(function (d: any) {
					d.data._included = true;
					return d;
				});
		}

		//Recalculate our events on this subscription
		matchingSubscription.events = this.workingEvents.filter(we => we.isChecked).map(we => we.name);

		//If no more events are checked under this subscription, remove it.
		if (!matchingSubscription.events.length) {
			const indexToDelete = this.workingCase.subscriptions.indexOf(matchingSubscription);
			this.workingCase.subscriptions.splice(indexToDelete, 1);

			//style the node in d3 as well
			d3.select('svg#caseSubscriptionsTree').select(`g.node#${this.getUid(this.selectedNode)}`)
				.classed('included', false)
				.datum((d: any) => {
					d.data._included = false;
					return d;
				});
		}
	}

	getUid(nodeData: { id: number, type: string }): string {
		return `uid-${nodeData.type}-${nodeData.id}`;
	}

	submit(): void {
		const validationMessage = this.validate();
		if (validationMessage) {
			this.toastyService.error(validationMessage);
			return;
		}

		//If case has an ID, case already exists, call update
		if (this.workingCase.id) {
			this.casesService
				.editCase(this.workingCase)
				.then(c => this.activeModal.close({
					case: c,
					isEdit: true,
				}))
				.catch(e => this.toastyService.error(e.message));
		} else {
			this.casesService
				.addCase(this.workingCase)
				.then(c => this.activeModal.close({
					case: c,
					isEdit: false,
				}))
				.catch(e => this.toastyService.error(e.message));
		}
	}

	validate(): string {
		return '';
	}
}
