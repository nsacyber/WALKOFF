import { Component } from '@angular/core';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';

import { ControllerService } from './controller.service';

import { AvailableSubscription } from '../models/availableSubscription';
import { Case } from '../models/case';
import { Workflow } from '../models/workflow';

@Component({
	selector: 'controller-component',
	templateUrl: 'client/controller/controller.html',
	styleUrls: [
		'client/controller/controller.css',
	],
	providers: [ControllerService]
})
export class ControllerComponent {
	currentController: string;
	schedulerStatus: string;
	availableSubscriptions: AvailableSubscription[];
	cases: Case[];

	// @ViewChild(ContextMenuComponent) public basicMenu: ContextMenuComponent; 

	constructor(private controllerService: ControllerService, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.currentController = "Default Controller";

		// this.getAvailableSubscriptions();
		// this.getCases();
		this.getSchedulerStatus();
	}

	getAvailableSubscriptions(): void {
		this.controllerService
			.getAvailableSubscriptions()
			.then(availableSubscriptions => this.availableSubscriptions = availableSubscriptions)
			.catch(e => this.toastyService.error(`Error retrieving available subscriptions: ${e.message}`));
	}

	getCases(): void {
		this.controllerService
			.getCases()
			.then(cases => this.cases = cases);
	}

	getSchedulerStatus(): void {
		this.controllerService
			.getSchedulerStatus()
			.then(schedulerStatus => this.schedulerStatus = schedulerStatus)
			.catch(e => this.toastyService.error(`Error retrieving scheduler status: ${e.message}`));
	}
	
	addCase(): void {
		//let id = Object.keys($("#casesTree").jstree()._model.data).length;
		//let name = "case_" + id;
		//$("#casesTree").jstree().create_node("#", {"id": name, "text" : name, "type":"case", "icon": "jstree-file"}, "last", function(){});

		this.controllerService
			.addCase(name)
			.then(newCase => this.cases.push(newCase));
	}

	changeSchedulerStatus(status: string): void {
		if (status === 'start' && this.schedulerStatus === 'paused') status = 'resume';

		this.controllerService
			.changeSchedulerStatus(status)
			.then((newStatus) => {
				if (newStatus) this.schedulerStatus = newStatus;
			})
			.catch(e => this.toastyService.error(`Error changing scheduler status: ${e.message}`));
	}

	executeWorkflow(workflow: Workflow): void {
		this.controllerService
			.executeWorkflow(workflow.name, workflow.name)
			.then(() => this.toastyService.success(`Workflow ${workflow.name} has been scheduled to execute.`))
			.catch(e => this.toastyService.error(`Error executing workflow: ${e.message}`));
	}

	// notifyMe() : void {
	// 	if (!Notification) {
	// 		console.log('Desktop notifications not available in your browser. Try Chromium.');
	// 	}
	// 	else if (Notification.permission !== "granted") Notification.requestPermission();
	// 	else {
	// 		var notification = new Notification('WALKOFF event', {
	// 			icon: 'http://cdn.sstatic.net/stackexchange/img/logos/so/so-icon.png',
	// 			body: "workflow was executed!",
	// 		});

	// 		notification.onclick = function () {
	// 			window.open("https://github.com/iadgov");
	// 		};
	// 	}
	// }

	canStart() : boolean {
		return this.schedulerStatus !== 'running';
	}

	canStop() : boolean {
		return this.schedulerStatus !== 'stopped';
	}
	
	canPause() : boolean {
		return this.schedulerStatus === 'running';
	}
}