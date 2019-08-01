import { Component, Input, ViewChild } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { NgForm } from '@angular/forms';

@Component({
    selector: 'import-modal-component',
    templateUrl: './import.modal.html',
})
export class ImportModalComponent {
    @ViewChild('myForm', { static: true })
    myForm: NgForm;
    submitted: boolean = false;
    importFile: File;
    
    constructor(public activeModal: NgbActiveModal) { }

    /**
	 * Sets our playbook to import based on a file input change.
	 * @param event JS Event for the playbook file input
	 */
	onImportSelectChange(event: Event) {
        this.importFile = (event.srcElement || event.target  as any).files[0];
        console.log(this.importFile)
	}
    
    submit() {
        this.submitted = true;
        if (this.importFile) this.activeModal.close(this.importFile);
    }
}