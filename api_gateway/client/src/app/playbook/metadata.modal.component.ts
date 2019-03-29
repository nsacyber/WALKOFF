import { Component, Input } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { Workflow } from '../models/playbook/workflow';

@Component({
    selector: 'metadata-modal-component',
    templateUrl: './metadata.modal.html',
})
export class MetadataModalComponent {
    @Input() workflow: Workflow = new Workflow();
    @Input() currentTags: string[] = ['UI', 'Automation', 'Bro'];
    existing: boolean = false;

    tagSelectOptions = {
        multiple: true,
        tags: true,
        width: '100%',
        placeholder: 'Add Tags...'
    };

    constructor(public activeModal: NgbActiveModal) { }

    tagsChanged($event: any): void {
        // Convert strings to numbers here
        console.log('Hihi', $event)
		this.workflow.tags = $event.value;
	}
}