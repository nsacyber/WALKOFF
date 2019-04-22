import { Component, Input, ViewChild } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { Workflow } from '../models/playbook/workflow';
import { NgForm } from '@angular/forms';

@Component({
    selector: 'metadata-modal-component',
    templateUrl: './metadata.modal.html',
})
export class MetadataModalComponent {
    @Input() workflow: Workflow = new Workflow();
    @Input() currentTags: string[] = [];

    @ViewChild('myForm')
    myForm: NgForm;
    existing: boolean = false;
    submitted: boolean = false;

    tagSelectOptions = {
        multiple: true,
        tags: true,
        width: '100%',
        placeholder: 'Add Tags...'
    };

    constructor(public activeModal: NgbActiveModal) { }

    tagsChanged($event: any): void {
		this.workflow.tags = $event.value;
    }
    
    submit() {
        this.submitted = true;
        if (this.myForm.valid) this.activeModal.close(this.workflow);
    }
}