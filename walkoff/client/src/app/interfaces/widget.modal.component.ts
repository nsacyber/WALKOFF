import { Component, OnInit, Input } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { InterfaceWidget } from '../models/interface/interfaceWidget';
import { ExecutionService } from '../execution/execution.service';

@Component({
    selector: 'widget-modal-component',
    templateUrl: './widget.modal.component.html',
    styleUrls: ['./widget.modal.component.scss']
})
export class WidgetModalComponent implements OnInit {

    @Input() widget: InterfaceWidget;

    availableWorkflows: any[] = [];

    constructor(public activeModal: NgbActiveModal, private executionService: ExecutionService) { }

    ngOnInit() {
        this.executionService
            .getPlaybooks()
            .then(playbooks => {
                playbooks.forEach(playbook => {
                    playbook.workflows.forEach(workflow => {
                        this.availableWorkflows.push({
                            id: workflow.id,
                            text: `${playbook.name} - ${workflow.name}`,
                        });
                    });
                });
            });
    }
}
