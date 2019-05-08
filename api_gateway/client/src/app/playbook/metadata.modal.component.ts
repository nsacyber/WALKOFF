import { Component, Input, ViewChild } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { Workflow } from '../models/playbook/workflow';
import { NgForm, NgModel } from '@angular/forms';

@Component({
    selector: 'metadata-modal-component',
    templateUrl: './metadata.modal.html',
})
export class MetadataModalComponent {
    @Input() workflow: Workflow = new Workflow();
    @Input() existingWorkflows: Workflow[] = [];
    @Input() currentTags: string[] = [];
    @Input() existing: boolean = false;

    @ViewChild('myForm')
    myForm: NgForm;

    @ViewChild('workflowName') 
    workflowNameModel: NgModel;

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
        if (this.workflow.name && this.existingWorkflows.find(w => {
            return w.name.toLocaleLowerCase() == this.workflow.name.toLocaleLowerCase() && w.id != this.workflow.id;
        })) {
            this.workflowNameModel.control.setErrors({'unique': true});
        }

        if (this.myForm.valid) this.activeModal.close(this.workflow);
    }
}