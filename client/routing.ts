import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { DashboardComponent }	from './dashboard/dashboard.component';
import { PlaybookComponent }	from './playbook/playbook.component';
import { SchedulerComponent }	from './scheduler/scheduler.component';
import { DevicesComponent }		from './devices/devices.component';
import { TriggersComponent }	from './triggers/triggers.component';
import { CasesComponent }	from './cases/cases.component';
import { SettingsComponent }	from './settings/settings.component';
// import { AppsComponent }	from './apps/apps.component';
//etc

const routes: Routes = [
	{ path: '', redirectTo: '/playbook', pathMatch: 'full' },
	{ path: 'dashboard', component: DashboardComponent },
	{ path: 'playbook', component: PlaybookComponent },
	{ path: 'scheduler', component: SchedulerComponent },
	{ path: 'devices', component: DevicesComponent },
	{ path: 'triggers', component: TriggersComponent },
	{ path: 'cases', component: CasesComponent },
	{ path: 'settings', component: SettingsComponent },
	// { path: 'apps/:app', component: AppsComponent },
	//etc
];

@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule]
})
export class RoutingModule {}