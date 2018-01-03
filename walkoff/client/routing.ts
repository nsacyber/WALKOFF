import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { DashboardComponent } from './dashboard/dashboard.component';
import { PlaybookComponent } from './playbook/playbook.component';
import { SchedulerComponent } from './scheduler/scheduler.component';
import { DevicesComponent } from './devices/devices.component';
import { MessagesComponent } from './messages/messages.component';
import { CasesComponent } from './cases/cases.component';
import { SettingsComponent } from './settings/settings.component';
import { InterfacesComponent } from './interfaces/interfaces.component';
//etc

const routes: Routes = [
	{ path: '', redirectTo: '/playbook', pathMatch: 'full' },
	{ path: 'dashboard', component: DashboardComponent },
	{ path: 'playbook', component: PlaybookComponent },
	{ path: 'scheduler', component: SchedulerComponent },
	{ path: 'devices', component: DevicesComponent },
	{ path: 'messages', component: MessagesComponent },
	{ path: 'cases', component: CasesComponent },
	{ path: 'settings', component: SettingsComponent },
	{ path: 'interfaces/:interfaceName', component: InterfacesComponent },
	//etc
];

@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule],
})
export class RoutingModule {}
