import { Component } from '@angular/core';
// import { FormControl } from '@angular/forms';
// import * as _ from 'lodash';
// import { NgbModal, NgbActiveModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
// import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';
// import { Select2OptionData } from 'ng2-select2';

// import { TriggersModalComponent } from './triggers.modal.component';

import { TriggersService } from './triggers.service';

import { Trigger } from '../models/trigger';

@Component({
	selector: 'triggers-component',
	templateUrl: 'client/triggers/triggers.html',
	styleUrls: [
		'client/triggers/triggers.css',
	],
	providers: [TriggersService]
})
export class TriggersComponent {
	//TODO: Component simply loads old main.js (with plugins and some tweaks). Will update or remove later.
	constructor() {	}

	ngAfterViewInit() {
		let removeScript = () => {
			let indx = 0;
			while (indx < document.body.childNodes.length) {
				if ('localName' in document.body.childNodes[indx]
					&& document.body.childNodes[indx].localName == 'script') {
						document.body.removeChild(document.body.childNodes[indx]);
				} else {
					indx++;
				}
			}

			var headStyleAll = document.head.querySelectorAll("style");
			for (let indxStr in headStyleAll) {
				let headStyle = headStyleAll[parseInt(indxStr)];
				console.log(headStyle);
				if (headStyle != null && headStyle.innerText.indexOf('palette') > -1) {
					document.head.removeChild(headStyle);
					break;
				}
			}
		}

		let addScript = (script: string) => {
			let s = document.createElement("script");
			s.type = "text/javascript";
			s.src = script;
			s.async = false;
			document.body.appendChild(s);
		}

		let addLink = (script: string) => {
			let s = document.createElement("link");
			s.rel = "stylesheet";
			s.href = script;
			document.body.appendChild(s);
		}

		removeScript();

		addLink('client/node_modules/jqueryui/jquery-ui.min.css');

		addScript("client/node_modules/jquery-migrate/dist/jquery-migrate.min.js");
		addScript("client/node_modules/jqueryui/jquery-ui.min.js");
		addScript("client/node_modules/json-editor/dist/jsoneditor.min.js");
		addScript("client/playbook/plugins/notifyjs/notify.min.js");
		addScript("client/triggers/main.js");
	}

	//Trigger Data Table params
	// triggers: Trigger[] = [];
	// displayTriggers: Trigger[] = [];
	// appNames: string[] = [];
	// availableApps: Select2OptionData[] = [];
	// appSelectConfig: Select2Options;
	// selectedApps: string[] = [];
	// filterQuery: FormControl = new FormControl();

	// constructor(private triggersService: TriggersService, private modalService: NgbModal, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
	// 	this.toastyConfig.theme = 'bootstrap';
	// }

	// filterTriggers(): void {
	// 	let searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

	// 	this.displayTriggers = this.triggers.filter((trigger) => {
	// 		return trigger.name.toLocaleLowerCase().includes(searchFilter);
	// 	});
	// }

	// getTriggers(): void {
	// 	this.triggersService
	// 		.getTriggers()
	// 		.then(triggers => this.displayTriggers = this.triggers = triggers)
	// 		.catch(e => this.toastyService.error(`Error retrieving triggers: ${e.message}`));

	// }

	// addTrigger(): void {
	// 	const modalRef = this.modalService.open(TriggersModalComponent);
	// 	modalRef.componentInstance.title = 'Add New Trigger';
	// 	modalRef.componentInstance.submitText = 'Add Trigger';

	// 	this._handleModalClose(modalRef);
	// }

	// editTrigger(trigger: Trigger): void {
	// 	const modalRef = this.modalService.open(TriggersModalComponent);
	// 	modalRef.componentInstance.title = `Edit Trigger ${trigger.name}`;
	// 	modalRef.componentInstance.submitText = 'Save Changes';

	// 	modalRef.componentInstance.workingTrigger = _.cloneDeep(trigger);

	// 	this._handleModalClose(modalRef);
	// }

	// private _handleModalClose(modalRef: NgbModalRef): void {
	// 	modalRef.result
	// 		.then((result) => {
	// 			//Handle modal dismiss
	// 			if (!result || !result.trigger) return;

	// 			//On edit, find and update the edited item
	// 			if (result.isEdit) {
	// 				let toUpdate = _.find(this.triggers, d => d.id === result.trigger.id);
	// 				Object.assign(toUpdate, result.trigger);

	// 				this.toastyService.success(`Trigger "${result.trigger.name}" successfully edited.`);
	// 			}
	// 			//On add, push the new item
	// 			else {
	// 				this.triggers.push(result.trigger);
	// 				this.toastyService.success(`Trigger "${result.trigger.name}" successfully added.`);
	// 			}
	// 		},
	// 		(error) => { if (error) this.toastyService.error(error.message); });
	// }

	// deleteTrigger(triggerToDelete: Trigger): void {
	// 	if (!confirm(`Are you sure you want to delete the trigger "${triggerToDelete.name}"?`)) return;

	// 	this.triggersService
	// 		.deleteTrigger(triggerToDelete.id)
	// 		.then(() => {
	// 			this.triggers = _.reject(this.triggers, trigger => trigger.id === triggerToDelete.id);

	// 			this.toastyService.success(`Trigger "${triggerToDelete.name}" successfully deleted.`);
	// 		})
	// 		.catch(e => this.toastyService.error(`Error deleting trigger: ${e.message}`));
	// }
}