import { Component, Input, ViewChild } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { NgForm } from '@angular/forms';
import { UtilitiesService } from '../utilities.service';

@Component({
    selector: 'file-modal-component',
    templateUrl: './file.modal.html',
})
export class FileModalComponent {
    @ViewChild('myForm', { static: true })
    myForm: NgForm;
    path: string;
    submitted: boolean = false;
    importFile: File;
    
    constructor(public activeModal: NgbActiveModal, public utils: UtilitiesService) { }

    /**
	 * Sets our playbook to import based on a file input change.
	 * @param event JS Event for the playbook file input
	 */
	onImportSelectChange(event: Event) {
        this.importFile = (event.srcElement || event.target  as any).files[0];
        console.log(this.importFile)
	}
    
    async submit() {
        this.submitted = true;
        if (this.importFile) {
            const body = await this.utils.readUploadedFileAsText(this.importFile);
            this.activeModal.close({ path: this.importFile.name, body});
        }
    }
}