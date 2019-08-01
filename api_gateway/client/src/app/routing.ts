import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { PlaybookComponent } from './playbook/playbook.component';
import { SchedulerComponent } from './scheduler/scheduler.component';
import { GlobalsComponent } from './globals/globals.component';
import { MessagesComponent } from './messages/messages.component';
import { MetricsComponent } from './metrics/metrics.component';
import { SettingsComponent } from './settings/settings.component';
import { ReportsComponent } from './reports/reports.component';
import { ExecutionComponent } from './execution/execution.component';
import { ManageReportsComponent } from './reports/manage.reports.component';
import { WorkflowEditorComponent } from './playbook/workflow.editor.component';
//etc

const routes: Routes = [
	{ path: '', redirectTo: '/workflows', pathMatch: 'full' },
	{ path: 'workflows', component: PlaybookComponent },
	{ path: 'workflows/new', component: WorkflowEditorComponent },
	{ path: 'workflows/:workflowId', component: WorkflowEditorComponent },
	{ path: 'scheduler', component: SchedulerComponent },
	{ path: 'globals', component: GlobalsComponent },
	{ path: 'settings', component: SettingsComponent },
	{ path: 'execution', component: ExecutionComponent },
	{ path: 'report/new', component: ManageReportsComponent },
	{ path: 'report/:reportId/edit', component: ManageReportsComponent },
	{ path: 'report/:reportId', component: ReportsComponent },
];

@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule],
})
export class RoutingModule {}
