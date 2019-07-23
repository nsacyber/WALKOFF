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

    @ViewChild('myForm', { static: true })
    myForm: NgForm;

    @ViewChild('workflowName', { static: true }) 
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
        const compareWorkflow = (w: Workflow) => 
            w.name.toLocaleLowerCase() == this.workflow.name.toLocaleLowerCase() && w.id != this.workflow.id;

        if (!this.workflow.name) {
            this.workflowNameModel.control.setErrors({'required': true});
        }
        else if (this.existingWorkflows.find(compareWorkflow)) {
            this.workflowNameModel.control.setErrors({'unique': true});
        }

        if (this.myForm.valid) this.activeModal.close(this.workflow);
    }
}