import { Component, ViewEncapsulation, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { VariableModalComponent } from './variable.modal.component';
import { GlobalsService } from './globals.service';
import { Variable } from '../models/variable';

import { classToClass } from 'class-transformer';
import { UtilitiesService } from '../utilities.service';

@Component({
	selector: 'globals-component',
	templateUrl: './globals.html',
	styleUrls: [
		'./globals.scss',
	],
	encapsulation: ViewEncapsulation.None,
})
export class GlobalsComponent implements OnInit {
	//Global Data Table params
	globals: Variable[] = [];
	filterQuery: FormControl = new FormControl();

	constructor(
		private globalsService: GlobalsService, private modalService: NgbModal, 
		private toastrService: ToastrService, private utils: UtilitiesService,
	) {}

	/**
	 * On component init, initialize the app select2 config, grab globals and global apis from the server.
	 * Set up the search filter to filter globals after 500 ms of inactivity.
	 */
	ngOnInit(): void {
		this.globalsService.globalsChange.subscribe(globals => this.globals = globals);
	}

	/**
	 * Filters globals based on the selected apps select2, and the value of the search filter input box.
	 * If no apps are selected, assume all apps should be returned.
	 */
	get filteredGlobals(): Variable[] {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';
		return this.globals.filter(global => 
			global.name.toLocaleLowerCase().includes(searchFilter) ||
			global.value.toLocaleLowerCase().includes(searchFilter) ||
			(global.description && global.description.toLocaleLowerCase().includes(searchFilter))
		)
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
}
