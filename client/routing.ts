import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ControllerComponent }	from './controller/controller.component';
import { LoginComponent }	from './login/login.component';
import { DashboardComponent }	from './dashboard/dashboard.component';
import { PlaybookComponent }	from './playbook/playbook.component';
import { DevicesComponent }		from './devices/devices.component';
import { TriggersComponent }	from './triggers/triggers.component';
import { CasesComponent }	from './cases/cases.component';
import { SettingsComponent }	from './settings/settings.component';
//etc

const routes: Routes = [
	{ path: '', redirectTo: '/dashboard', pathMatch: 'full' },
//	{ path: 'login', component: LoginComponent },
	{ path: 'dashboard', component: DashboardComponent },
	{ path: 'controller', component: ControllerComponent },
	{ path: 'playbook', component: PlaybookComponent },
	{ path: 'devices', component: DevicesComponent },
	{ path: 'triggers', component: TriggersComponent },
	{ path: 'cases', component: CasesComponent },
	{ path: 'settings', component: SettingsComponent },
	//etc
];

@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule]
})
export class RoutingModule {}