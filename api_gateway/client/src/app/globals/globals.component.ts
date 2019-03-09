import { Component, ViewEncapsulation, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { Select2OptionData } from 'ng2-select2';

import { GlobalsModalComponent } from './globals.modal.component';

import { GlobalsService } from './globals.service';

import { Global } from '../models/global';
import { WorkingGlobal } from '../models/workingGlobal';
import { AppApi } from '../models/api/appApi';
import { GenericObject } from '../models/genericObject';

@Component({
	selector: 'globals-component',
	templateUrl: './globals.html',
	styleUrls: [
		'./globals.scss',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [GlobalsService],
})
export class GlobalsComponent implements OnInit {
	//Global Data Table params
	globals: Global[] = [];
	displayGlobals: Global[] = [];
	appNames: string[] = [];
	availableApps: Select2OptionData[] = [];
	appSelectConfig: Select2Options;
	appApis: AppApi[] = [];
	selectedApps: string[] = [];
	filterQuery: FormControl = new FormControl();

	constructor(
		private globalsService: GlobalsService, private modalService: NgbModal, 
		private toastrService: ToastrService,
	) {}

	/**
	 * On component init, initialize the app select2 config, grab globals and global apis from the server.
	 * Set up the search filter to filter globals after 500 ms of inactivity.
	 */
	ngOnInit(): void {

		this.appSelectConfig = {
			width: '100%',
			multiple: true,
			allowClear: true,
			placeholder: 'Filter by app(s)...',
			closeOnSelect: false,
		};

		this.getGlobals();
		this.getGlobalApis();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterGlobals());
	}

	/**
	 * Fired when apps are selected in the select2 box. Calls filter globals which filters based on the selected apps.
	 * @param event	JS event from select2 for app selection.
	 */
	appSelectChange(event: any): void {
		this.selectedApps = event.value;
		this.filterGlobals();
	}

	/**
	 * Filters globals based on the selected apps select2, and the value of the search filter input box.
	 * If no apps are selected, assume all apps should be returned.
	 */
	filterGlobals(): void {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayGlobals = this.globals.filter(global => {
			return (global.name.toLocaleLowerCase().includes(searchFilter) ||
				global.app_name.toLocaleLowerCase().includes(searchFilter)) &&
				(this.selectedApps.length ? this.selectedApps.indexOf(global.app_name) > -1 : true);
		});
	}

	/**
	 * Gets an array of globals from the server/DB and sets them for display in our data table.
	 */
	getGlobals(): void {
		this.globalsService
			.getAllGlobals()
			.then(globals => this.displayGlobals = this.globals = globals)
			.catch(e => this.toastrService.error(`Error retrieving globals: ${e.message}`));
	}

	/**
	 * Spawns a modal for adding a new global. Passes in the app names and apis for usage in the modal.
	 */
	addGlobal(): void {
		const modalRef = this.modalService.open(GlobalsModalComponent);
		modalRef.componentInstance.title = 'Add New Global';
		modalRef.componentInstance.submitText = 'Add Global';
		modalRef.componentInstance.appNames = this.appNames;
		modalRef.componentInstance.appApis = this.appApis;

		this._handleModalClose(modalRef);
	}

	/**
	 * Spawns a modal for editing an existing global. Passes in the app names and apis for usage in the modal.
	 */
	editGlobal(global: Global): void {
		const modalRef = this.modalService.open(GlobalsModalComponent);
		modalRef.componentInstance.title = `Edit Global ${global.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.appNames = this.appNames;
		modalRef.componentInstance.appApis = this.appApis;
		modalRef.componentInstance.workingGlobal = WorkingGlobal.fromGlobal(global);

		this._handleModalClose(modalRef);
	}

	/**
	 * After user confirmation, will delete a given global from the database.
	 * Removes it from our list of globals to display.
	 * @param globalToDelete Global to delete
	 */
	deleteGlobal(globalToDelete: Global): void {
		if (!confirm(`Are you sure you want to delete the global "${globalToDelete.name}"?`)) { return; }

		this.globalsService
			.deleteGlobal(globalToDelete.id)
			.then(() => {
				this.globals = this.globals.filter(global => global.id !== globalToDelete.id);

				this.filterGlobals();

				this.toastrService.success(`Global "${globalToDelete.name}" successfully deleted.`);
			})
			.catch(e => this.toastrService.error(`Error deleting global: ${e.message}`));
	}

	/**
	 * Gets an array of AppApi objects which only contain their GlobalApis.
	 * AppApis are passed into the add/edit modal to handle custom global fields.
	 * Also builds the available apps data for the app select2.
	 */
	getGlobalApis(): void {
		this.globalsService
			.getGlobalApis()
			.then(appApis => {
				this.appApis = appApis;
				this.appNames = appApis.map(a => a.name);
				this.availableApps = this.appNames.map((appName) => ({ id: appName, text: appName }));
			})
			.catch(e => this.toastrService.error(`Error retrieving global types: ${e.message}`));
	}

	/**
	 * Gets a string representation of the custom fields specified on a global.
	 * Removes quotations for easier reading.
	 * @param global Global to build a custom fields string for
	 */
	getCustomFields(global: Global): string {
		const obj: GenericObject = {};
		global.fields.forEach(element => {
			if (element.value) { obj[element.name] = element.value; }
		});
		let out = JSON.stringify(obj, null, 1);
		out = out.substr(1, out.length - 2).replace(/"/g, '');
		return out;
	}

	/**
	 * On closing an add/edit modal (on clicking save), we will add or update existing globals for display.
	 * @param modalRef ModalRef that is being closed
	 */
	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.global) { return; }

				//On edit, find and update the edited item
				if (result.isEdit) {
					const toUpdate = this.globals.find(d => d.id === result.global.id);
					Object.assign(toUpdate, result.global);

					this.filterGlobals();

					this.toastrService.success(`Global "${result.global.name}" successfully edited.`);
				} else {
					this.globals.push(result.global);

					this.filterGlobals();

					this.toastrService.success(`Global "${result.global.name}" successfully added.`);
				}
			},
			(error) => { if (error) { this.toastrService.error(error.message); } });
	}
}
