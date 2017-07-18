import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule }   from '@angular/forms';
import { HttpModule } from '@angular/http';
// import { DataTableModule } from 'angular2-datatable';
import { NgbRootModule } from '@ng-bootstrap/ng-bootstrap';

// Custom routing module
import { RoutingModule } from './routing';
import { MainComponent } from './main/main.component';
import { ControllerComponent } from './controller/controller.component';
import { CasesComponent } from './cases/cases.component';
import { SettingsComponent } from './settings/settings.component';
import { SettingsUserModalComponent } from './settings/settings.user.modal.component';

@NgModule({
	imports: [
		BrowserModule,
		FormsModule,
		HttpModule,
		RoutingModule,
		// DataTableModule,
		NgbRootModule
	],
	declarations: [
		//Main component
		MainComponent,
		//Router module components
		ControllerComponent,
		CasesComponent,
		SettingsComponent,
		//Modals
		SettingsUserModalComponent,
	],
	entryComponents: [
		SettingsUserModalComponent
	],
	bootstrap: [MainComponent]
})
export class MainModule {}