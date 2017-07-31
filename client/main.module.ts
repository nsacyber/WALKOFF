import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule }   from '@angular/forms';
import { HttpModule } from '@angular/http';
// import { DataTableModule } from 'angular2-datatable';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { ToastyModule } from 'ng2-toasty';
import { Select2Module } from 'ng2-select2';

// Custom routing module
import { RoutingModule } from './routing';
import { MainComponent } from './main/main.component';
import { ControllerComponent } from './controller/controller.component';
import { PlaybookComponent } from './playbook/playbook.component';
import { DevicesComponent } from './devices/devices.component';
import { CasesComponent } from './cases/cases.component';
import { SettingsComponent } from './settings/settings.component';

import { DevicesModalComponent } from './devices/devices.modal.component';
import { SettingsUserModalComponent } from './settings/settings.user.modal.component';

@NgModule({
	imports: [
		BrowserModule,
		FormsModule,
		ReactiveFormsModule,
		HttpModule,
		RoutingModule,
		NgbModule.forRoot(),
		NgxDatatableModule,
		ToastyModule.forRoot(),
		Select2Module,
	],
	declarations: [
		//Main component
		MainComponent,
		//Router module components
		ControllerComponent,
		PlaybookComponent,
		DevicesComponent,
		CasesComponent,
		SettingsComponent,
		//Modals
		DevicesModalComponent,
		SettingsUserModalComponent,
	],
	entryComponents: [
		DevicesModalComponent,
		SettingsUserModalComponent,
	],
	bootstrap: [MainComponent]
})
export class MainModule {}