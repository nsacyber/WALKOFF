import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { PlaybookComponent } from './playbook/playbook.component';
import { SchedulerComponent } from './scheduler/scheduler.component';
import { GlobalsComponent } from './globals/globals.component';
import { SettingsComponent } from './settings/settings.component';
import { ReportsComponent } from './reports/reports.component';
import { ExecutionComponent } from './execution/execution.component';
import { ManageReportsComponent } from './reports/manage.reports.component';
import { WorkflowEditorComponent } from './playbook/workflow.editor.component';
import { AppsListComponent } from './apps/apps.list.component';
import { ManageAppComponent } from './apps/manage.app.component';
//etc

import { CanDeactivateGuard }    from './can-deactivate.guard';
import { RedirectGuard } from './redirect.guard';

const routes: Routes = [
	{ path: '', redirectTo: '/workflows', pathMatch: 'full' },
	{ path: 'workflows', component: PlaybookComponent },
	{ path: 'workflows/new', component: WorkflowEditorComponent, canDeactivate: [CanDeactivateGuard] },
	{ path: 'workflows/:workflowId', component: WorkflowEditorComponent, canDeactivate: [CanDeactivateGuard] },
	{ path: 'settings/scheduler', component: SchedulerComponent },
	{ path: 'settings/globals', component: GlobalsComponent },
	{ path: 'settings/users', component: SettingsComponent },
	{ path: 'execution', component: ExecutionComponent },
	{ path: 'apps', component: AppsListComponent },
	{ path: 'apps/:appId', component: ManageAppComponent, canDeactivate: [CanDeactivateGuard] },
	{ path: 'report/new', component: ManageReportsComponent, canDeactivate: [CanDeactivateGuard] },
	{ path: 'report/:reportId/edit', component: ManageReportsComponent, canDeactivate: [CanDeactivateGuard] },
	{ path: 'report/:reportId', component: ReportsComponent },
	{ path: 'logout', canActivate: [RedirectGuard], component: RedirectGuard, data: { externalUrl: '/walkoff/login', logout: true }}
];

@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule],
})
export class RoutingModule {}
