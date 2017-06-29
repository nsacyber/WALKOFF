import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ControllerComponent }	from './controller/controller.component';
//etc

const routes: Routes = [
	{ path: '', redirectTo: '/controller', pathMatch: 'full' },
	{ path: 'dashboard', component: ControllerComponent },
	{ path: 'controller', component: ControllerComponent },
	//etc
];

@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule]
})
export class RoutingModule {}