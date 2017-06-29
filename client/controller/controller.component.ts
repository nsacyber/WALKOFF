import { Component } from '@angular/core';

import { ControllerService } from './controller.service';

import { AvailableSubscription } from './availableSubscription';
import { Case } from './case';

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

	constructor(private controllerService: ControllerService) {
		this.currentController = "Default Controller";

		this.getAvailableSubscriptions();
		this.getCases();
		this.getSchedulerStatus();
	}

	getAvailableSubscriptions(): void {
		this.controllerService
			.getAvailableSubscriptions()
			.then(availableSubscriptions => this.availableSubscriptions = availableSubscriptions);
	}

	getCases(): void {
		this.controllerService
			.getCases()
			.then(cases => this.cases = cases);
	}

	getSchedulerStatus(): void {
		this.controllerService
			.getSchedulerStatus()
			.then(schedulerStatus => this.schedulerStatus = schedulerStatus);
	}
	
	addCase(): void {
		//let id = Object.keys($("#casesTree").jstree()._model.data).length;
		//let name = "case_" + id;
		//$("#casesTree").jstree().create_node("#", {"id": name, "text" : name, "type":"case", "icon": "jstree-file"}, "last", function(){});

		this.controllerService
			.addCase(name)
			.then(newCase => this.cases.push(newCase));
	}

	notifyMe() : void {
		if (!Notification) {
			console.log('Desktop notifications not available in your browser. Try Chromium.');
		}
		else if (Notification.permission !== "granted") Notification.requestPermission();
		else {
			var notification = new Notification('WALKOFF event', {
				icon: 'http://cdn.sstatic.net/stackexchange/img/logos/so/so-icon.png',
				body: "workflow was executed!",
			});

			notification.onclick = function () {
				window.open("https://github.com/iadgov");
			};
		}
	}
}