import { Component } from '@angular/core';

import { ControllerService } from '../../services/controller';

@Component({
	selector: 'controller-component',
	templateUrl: 'client/components/controller/controller.html',
	styleUrls: [
		'client/components/controller/controller.css',
	],
	providers: [ControllerService]
})
export class ControllerComponent {
	currentController: string;

	constructor(private controllerService: ControllerService) {
		this.currentController = "New Controller";
	}
}