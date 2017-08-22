import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule }   from '@angular/forms';
import { HttpModule } from '@angular/http';
// import { DataTableModule } from 'angular2-datatable';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { ToastyModule } from 'ng2-toasty';
import { Select2Module } from 'ng2-select2';
// import { ContextMenuModule } from 'ngx-contextmenu';

// Custom routing module
import { RoutingModule } from './routing';
import { MainComponent } from './main/main.component';
import { LoginComponent } from './login/login.component';
import { ControllerComponent } from './controller/controller.component';
import { PlaybookComponent } from './playbook/playbook.component';
import { DevicesComponent } from './devices/devices.component';
import { TriggersComponent } from './triggers/triggers.component';
import { CasesComponent } from './cases/cases.component';
import { SettingsComponent } from './settings/settings.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { DevicesModalComponent } from './devices/devices.modal.component';
import { CasesModalComponent } from './cases/cases.modal.component';
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
		// ContextMenuModule
	],
	declarations: [
		//Main component
		MainComponent,
		LoginComponent,

		//Router module components
		ControllerComponent,
		PlaybookComponent,
		DashboardComponent,
		DevicesComponent,
		TriggersComponent,
		CasesComponent,
		SettingsComponent,

		//Modals
		DevicesModalComponent,
		CasesModalComponent,
		SettingsUserModalComponent,
	],
	entryComponents: [
		DevicesModalComponent,
		CasesModalComponent,
		SettingsUserModalComponent,
	],
	bootstrap: [MainComponent]
})
export class MainModule {}