import { Component, OnInit, Input } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { InterfaceWidget } from '../models/interface/interfaceWidget';
import { ExecutionService } from '../execution/execution.service';
import { PlaybookService } from '../playbook/playbook.service';

@Component({
    selector: 'widget-modal-component',
    templateUrl: './widget.modal.component.html',
    styleUrls: ['./widget.modal.component.scss']
})
export class WidgetModalComponent implements OnInit {

    @Input() widget: InterfaceWidget;

    workflows: any[] = [];
    executions: any[] = [];
    actionResults: any[] = [];

    constructor(public activeModal: NgbActiveModal, private executionService: ExecutionService, private playbookService: PlaybookService) { }

    ngOnInit() {
        this.updateWorkflows();
        if (this.widget.options.workflow) {
            this.updateExecutions();
        }
    }

    async updateWorkflows() {
        const playbooks = await this.executionService.getPlaybooks();
        const workflows = [];
        playbooks.forEach(playbook => {
            playbook.workflows.forEach(workflow => {
                workflows.push({
                    id: workflow.id,
                    text: `${playbook.name} - ${workflow.name}`,
                });
            });
        });
        this.workflows = workflows;
    }

    async updateExecutions() {
        const workflowId = this.widget.options.workflow;
        const workflowStatuses = await this.executionService.getAllWorkflowStatuses();
        this.executions = [{id: 'latest', text: 'Latest'}].concat(workflowStatuses
                            .filter(status => status.workflow_id == workflowId && status.status == 'completed')
                            .map(status => ({ id: status.execution_id, text: status.completed_at_local})))

        this.widget.options.execution = 'latest';
        this.updateActionResults();
    }

    async updateActionResults() {
        const workflowId = this.widget.options.workflow;
        const executionId = this.widget.options.execution;

        if (executionId == 'latest') {
            const workflow = await this.playbookService.loadWorkflow(workflowId);
            this.actionResults = workflow.actions.map(action => ({ id: action.id, text: action.name }));
        }
        else {
            const workflowStatus = await this.executionService.getWorkflowStatus(executionId);
            this.actionResults = workflowStatus.action_statuses.map(status => ({ id: status.action_id, text: status.name }));
        }

        if (this.actionResults.length > 0)
            this.widget.options.action = this.actionResults[0].id;
    }
}
