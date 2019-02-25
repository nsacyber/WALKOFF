import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { PlaybookComponent } from './playbook/playbook.component';
import { SchedulerComponent } from './scheduler/scheduler.component';
import { DevicesComponent } from './devices/devices.component';
import { MessagesComponent } from './messages/messages.component';
import { MetricsComponent } from './metrics/metrics.component';
import { SettingsComponent } from './settings/settings.component';
import { InterfacesComponent } from './interfaces/interfaces.component';
import { ExecutionComponent } from './execution/execution.component';
import { ManageInterfacesComponent } from './interfaces/manage.interfaces.component';
//etc

const routes: Routes = [
	{ path: '', redirectTo: '/playbook', pathMatch: 'full' },
	{ path: 'playbook', component: PlaybookComponent },
	{ path: 'scheduler', component: SchedulerComponent },
	{ path: 'devices', component: DevicesComponent },
	// { path: 'messages', component: MessagesComponent },
	// { path: 'metrics', component: MetricsComponent },
	{ path: 'settings', component: SettingsComponent },
	{ path: 'execution', component: ExecutionComponent },
	{ path: 'new-interface', component: ManageInterfacesComponent },
	{ path: 'edit-interface/:interfaceName', component: ManageInterfacesComponent },
	{ path: 'interface/:interfaceName', component: InterfacesComponent },
	//etc
];

@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule],
})
export class RoutingModule {}
