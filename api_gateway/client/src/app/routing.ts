import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { PlaybookComponent } from './playbook/playbook.component';
import { SchedulerComponent } from './scheduler/scheduler.component';
import { GlobalsComponent } from './globals/globals.component';
import { MessagesComponent } from './messages/messages.component';
import { MetricsComponent } from './metrics/metrics.component';
import { SettingsComponent } from './settings/settings.component';
import { DashboardsComponent } from './dashboards/dashboards.component';
import { ExecutionComponent } from './execution/execution.component';
import { ManageDashboardsComponent } from './dashboards/manage.dashboards.component';
import { WorkflowEditorComponent } from './playbook/workflow.editor.component';
import { BucketsComponent } from './buckets/buckets.component';
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
	{ path: 'dashboard/new', component: ManageDashboardsComponent },
	{ path: 'dashboard/:dashboardId/edit', component: ManageDashboardsComponent },
	{ path: 'dashboard/:dashboardId', component: DashboardsComponent },
	{ path: 'buckets', component: BucketsComponent },
];

@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule],
})
export class RoutingModule {}
