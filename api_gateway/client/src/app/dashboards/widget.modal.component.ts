import { Component, OnInit, Input } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { DashboardWidget } from '../models/dashboard/dashboardWidget';
import { ExecutionService } from '../execution/execution.service';
import { PlaybookService } from '../playbook/playbook.service';

@Component({
    selector: 'widget-modal-component',
    templateUrl: './widget.modal.component.html',
    styleUrls: ['./widget.modal.component.scss']
})
export class WidgetModalComponent implements OnInit {

    @Input() widget: DashboardWidget;
    typeLabel: string = 'Widget';

    workflows: any[] = [];
    executions: any[] = [];
    nodeResults: any[] = [];

    constructor(public activeModal: NgbActiveModal, private executionService: ExecutionService, private playbookService: PlaybookService) { }

    ngOnInit() {
        this.updateWorkflows();
        if (this.widget.options.workflow) {
            this.updateExecutions();
        }
    }

    async updateWorkflows() {
        const workflows = await this.executionService.getWorkflows();
        const workflowOptions = [];
        workflows.forEach(workflow => {
            workflowOptions.push({
                id: workflow.id,
                text: workflow.name,
            });
        });
        this.workflows = workflowOptions;
    }

    async updateExecutions() {
        const workflowId = this.widget.options.workflow;
        const workflowStatuses = await this.executionService.getAllWorkflowStatuses();
        this.executions = [{id: 'latest', text: 'Latest'}].concat(workflowStatuses
                            .filter(status => status.workflow_id == workflowId && status.status == 'completed')
                            .map(status => ({ id: status.execution_id, text: status.completed_at_local})))

        this.widget.options.execution = 'latest';
        this.updateNodeResults();
    }

    async updateNodeResults() {
        const workflowId = this.widget.options.workflow;
        const executionId = this.widget.options.execution;

        if (executionId == 'latest') {
            const workflow = await this.playbookService.loadWorkflow(workflowId);
            this.nodeResults = workflow.actions.map(action => ({ id: action.id, text: action.name }));
        }
        else {
            const workflowStatus = await this.executionService.getWorkflowStatus(executionId);
            this.nodeResults = workflowStatus.node_statuses.map(status => ({ id: status.node_id, text: status.name }));
        }

        if (this.nodeResults.length > 0)
            this.widget.options.action = this.nodeResults[0].id;
    }
}
