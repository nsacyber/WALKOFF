import { Component, Input, ViewEncapsulation } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';
import * as d3 from 'd3';

import { CasesService } from './cases.service';

import { Case } from '../models/case';
import { AvailableSubscription } from '../models/availableSubscription';
import { Subscription } from '../models/subscription';

@Component({
	encapsulation: ViewEncapsulation.None,
	selector: 'case-modal',
	templateUrl: 'client/cases/cases.modal.html',
	styleUrls: [
		'client/cases/cases.modal.css'
	],
	providers: [CasesService]
})
export class CasesModalComponent {
	@Input() workingCase: Case;
	@Input() title: string;
	@Input() submitText: string;
	@Input() availableSubscriptions: AvailableSubscription[] = [];
	@Input() subscriptionTree: any;
	@Input() workingEvents: { name: string, isChecked: boolean }[] = [];

	selectedNode: { name: string, uid: string, type: string } = { name: '', uid: '', type: '' };

	constructor(private casesService: CasesService, private activeModal: NgbActiveModal, private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';
	}

	ngOnInit(): void {
		let self = this;

		// Set the dimensions and margins of the diagram
		let margin = { top: 20, right: 90, bottom: 30, left: 90 },
			width = 1350 - margin.left - margin.right,
			height = 500 - margin.top - margin.bottom;

		// append the svg object to the body of the page
		// appends a 'group' element to 'svg'
		// moves the 'group' element to the top left margin
		let svg = d3.select("svg#caseSubscriptionsTree")//.append("svg")
			.attr("width", width + margin.right + margin.left)
			.attr("height", height + margin.top + margin.bottom)
			.append("g")
			.attr("transform", `translate(${margin.left},${margin.top})`);

		let i = 0,
			duration = 750,
			root: any;

		// declares a tree layout and assigns the size
		let treemap = d3.tree().size([height, width]);

		// Assigns parent, children, height, depth
		root = d3.hierarchy(self.subscriptionTree);
		root.x0 = height / 2;
		root.y0 = 0;

		// Collapse after the second level
		root.children.forEach(collapse);

		update(root);

		// Collapse the node and all it's children
		function collapse(d: any) {
			if (d.children) {
				d._children = d.children;
				d._children.forEach(collapse);
				d.children = null;
			}
		}

		function update(source: any) {

			// Assigns the x and y position for the nodes
			var treeData = treemap(root);

			// Compute the new tree layout.
			var nodes = treeData.descendants(),
				links = treeData.descendants().slice(1);

			// Normalize for fixed-depth.
			nodes.forEach(function (d) { d.y = d.depth * 180 });

			// ****************** Nodes section ***************************

			// Update the nodes...
			var node = svg.selectAll('g.node')
				.data(nodes, function (d: any) { return d.id || (d.id = ++i); });

			// Enter any new modes at the parent's previous position.
			var nodeEnter = node.enter().append('g')
				.attr('class', 'node')
				.attr("transform", function (d) {
					return "translate(" + source.y0 + "," + source.x0 + ")";
				})
				.on('click', click)
				.on('dblclick', dblclick);

			// Add Circle for the nodes
			nodeEnter.append('circle')
				.attr('class', 'node')
				.attr('r', 1e-6)
				.style("fill", function (d: any) {
					return d._children ? "lightsteelblue" : "#fff";
				});

			// Add labels for the nodes
			nodeEnter.append('text')
				.attr("dy", ".35em")
				.attr("x", function (d: any) {
					return d.children || d._children ? -13 : 13;
				})
				.attr("text-anchor", function (d: any) {
					return d.children || d._children ? "end" : "start";
				})
				.text(function (d: any) { return d.data.name; });

			// UPDATE
			var nodeUpdate = nodeEnter.merge(node);

			// Transition to the proper position for the node
			nodeUpdate.transition()
				.duration(duration)
				.attr("transform", function (d) {
					return "translate(" + d.y + "," + d.x + ")";
				});

			// Update the node attributes and style
			nodeUpdate.select('circle.node')
				.attr('r', 10)
				.style("fill", function (d: any) {
					return d._children ? "lightsteelblue" : "#fff";
				});

			// Remove any exiting nodes
			var nodeExit = node.exit().transition()
				.duration(duration)
				.attr("transform", function (d) {
					return "translate(" + source.y + "," + source.x + ")";
				})
				.remove();

			// On exit reduce the node circles size to 0
			nodeExit.select('circle')
				.attr('r', 1e-6);

			// On exit reduce the opacity of text labels
			nodeExit.select('text')
				.style('fill-opacity', 1e-6);

			// ****************** links section ***************************

			// Update the links...
			var link = svg.selectAll('path.link')
				.data(links, function (d: any) { return d.id; });

			// Enter any new links at the parent's previous position.
			var linkEnter = link.enter().insert('path', "g")
				.attr("class", "link")
				.attr('d', function (d) {
					var o = { x: source.x0, y: source.y0 }
					return diagonal(o, o)
				});

			// UPDATE
			var linkUpdate = linkEnter.merge(link);

			// Transition back to the parent element position
			linkUpdate.transition()
				.duration(duration)
				.attr('d', function (d) { return diagonal(d, d.parent) });

			// Remove any exiting links
			var linkExit = link.exit().transition()
				.duration(duration)
				.attr('d', function (d) {
					var o = { x: source.x, y: source.y }
					return diagonal(o, o)
				})
				.remove();

			// Store the old positions for transition.
			nodes.forEach(function (d: any) {
				d.x0 = d.x;
				d.y0 = d.y;
			});

			// Creates a curved (diagonal) path from parent to the child nodes
			function diagonal(s: any, d: any) {
				let path = `M ${s.y} ${s.x}
					C ${(s.y + d.y) / 2} ${s.x},
					${(s.y + d.y) / 2} ${d.x},
					${d.y} ${d.x}`;

				return path;
			}

			// Toggle children on double click.
			// function click(d: any) {
			function dblclick(d:any) {
				if (d.children) {
					d._children = d.children;
					d.children = null;
				} else {
					d.children = d._children;
					d._children = null;
				}
				update(d);
			}

			//Select our node on click
			// function dblclick(d: any) {
			function click(d: any) {
				if (!d.data.type) return;

				self.selectedNode = { name: d.data.name, uid: d.data.uid, type: d.data.type };

				let availableEvents = self.availableSubscriptions.find(function (a) {
					return d.data.type === a.type;
				}).events;

				let subscription = self.workingCase.subscriptions.find(function (s) {
					return d.data.uid === s.uid;
				});

				let subscriptionEvents = subscription ? subscription.events : [];

				self.workingEvents = [];

				availableEvents.forEach(function (event) {
					self.workingEvents.push({
						name: event,
						isChecked: subscriptionEvents.indexOf(event) > -1
					});
				});

				//Clear highlighting on other highlighted node(s)
				svg.selectAll('g.node.highlighted')
					.attr('class', 'node');

				//Highlight this node now.
				d3.select(this)
					.attr('class', 'node highlighted');
			}
		}
	}

	handleEventSelectionChange(event: any, isChecked: boolean): void {
		let self = this;

		if (!self.selectedNode.name) {
			console.log('Attempted to select events without a node selected.');
			return;
		}

		event.isChecked = isChecked;

		let matchingSubscription = self.workingCase.subscriptions.find(function (s) {
			return s.uid === self.selectedNode.uid;
		});

		//If no subscription is returned, it doesn't exist yet; add it.
		if (!matchingSubscription) {
			matchingSubscription = new Subscription();
			matchingSubscription.uid = self.selectedNode.uid;
			self.workingCase.subscriptions.push(matchingSubscription);
		}

		//Recalculate our events on this subscription
		matchingSubscription.events = self.workingEvents.filter(function (we) {
			return we.isChecked;
		}).map(function (we) {
			return we.name;
		});

		//If no more events are checked under this subscription, remove it.
		if (!matchingSubscription.events.length) {
			let indexToDelete = self.workingCase.subscriptions.indexOf(matchingSubscription);
			self.workingCase.subscriptions.splice(indexToDelete, 1);
		}

		console.log(self.workingCase);
		console.log(event);
	}

	submit(): void {
		let validationMessage = this.validate();
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
					isEdit: true
				}))
				.catch(e => this.toastyService.error(e.message));
		}
		else {
			this.casesService
				.addCase(this.workingCase)
				.then(c => this.activeModal.close({
					case: c,
					isEdit: false
				}))
				.catch(e => this.toastyService.error(e.message));
		}
	}

	validate(): string {
		return '';
	}
}