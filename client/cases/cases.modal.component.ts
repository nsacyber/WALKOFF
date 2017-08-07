import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';

import { CasesService } from './cases.service';

import { Case } from '../models/case';
 
@Component({
	selector: 'case-modal',
	templateUrl: 'client/cases/cases.modal.html',
	styleUrls: [
		'client/cases/cases.css'
	],
	providers: [CasesService]
})
export class CasesModalComponent {
	@Input() workingCase: Case;
	@Input() title: string;
	@Input() submitText: string;

	constructor(private casesService: CasesService, private activeModal: NgbActiveModal, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';
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