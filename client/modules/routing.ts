import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ControllerComponent }	from '../components/controller/controller';
//etc

const routes: Routes = [
	{ path: '', redirectTo: '/dashboard', pathMatch: 'full' },
	{ path: 'dashboard', component: ControllerComponent },
	{ path: 'controller', component: ControllerComponent },
	//etc
];

@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule]
})
export class RoutingModule {}