import { NgModule } from '@angular/core';
import { Http, RequestOptions } from '@angular/http';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { ToastyModule } from 'ng2-toasty';
import { Select2Module } from 'ng2-select2';
import { JwtHttp } from 'angular2-jwt-refresh';
import { DateTimePickerModule } from 'ng-pick-datetime';
import { DndModule } from 'ng2-dnd';

// Custom routing module
import { RoutingModule } from './routing';
import { GetJwtHttp } from './jwthttp.factory';
import { MainComponent } from './main/main.component';
import { SchedulerComponent } from './scheduler/scheduler.component';
import { PlaybookComponent } from './playbook/playbook.component';
import { DevicesComponent } from './devices/devices.component';
import { MessagesComponent } from './messages/messages.component';
import { MetricsComponent } from './metrics/metrics.component';
import { SettingsComponent } from './settings/settings.component';
import { InterfacesComponent } from './interfaces/interfaces.component';
import { ExecutionComponent } from './execution/execution.component';

import { SchedulerModalComponent } from './scheduler/scheduler.modal.component';
import { DevicesModalComponent } from './devices/devices.modal.component';
import { SettingsUserModalComponent } from './settings/settings.user.modal.component';
import { SettingsRoleModalComponent } from './settings/settings.roles.modal.component';
import { ExecutionVariableModalComponent } from './execution/execution.variable.modal.component';
import { PlaybookEnvironmentVariableModalComponent } from './playbook/playbook.environment.variable.modal.component';

import { PlaybookArgumentComponent } from './playbook/playbook.argument.component';
import { PlaybookConditionsComponent } from './playbook/playbook.conditions.component';
import { PlaybookTransformsComponent } from './playbook/playbook.transforms.component';
import { PlaybookConditionalExpressionComponent } from './playbook/playbook.conditional.expression.component';
import { SettingsRolesComponent } from './settings/settings.roles.component';
import { MessagesModalComponent } from './messages/messages.modal.component';

import { KeysPipe } from './pipes/keys.pipe';

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
		DateTimePickerModule,
		DndModule.forRoot(),
	],
	declarations: [
		//Main component
		MainComponent,
		//Router module components
		PlaybookComponent,
		SchedulerComponent,
		DevicesComponent,
		MessagesComponent,
		MetricsComponent,
		SettingsComponent,
		InterfacesComponent,
		ExecutionComponent,
		//Modals
		SchedulerModalComponent,
		DevicesModalComponent,
		SettingsUserModalComponent,
		SettingsRoleModalComponent,
		MessagesModalComponent,
		PlaybookEnvironmentVariableModalComponent,
		ExecutionVariableModalComponent,
		// Other subcomponents
		PlaybookArgumentComponent,
		PlaybookConditionsComponent,
		PlaybookTransformsComponent,
		PlaybookConditionalExpressionComponent,
		SettingsRolesComponent,
		// Pipes
		KeysPipe,
	],
	providers: [{
		provide: JwtHttp,
		useFactory: GetJwtHttp,
		deps: [ Http, RequestOptions ],
	}],
	entryComponents: [
		SchedulerModalComponent,
		DevicesModalComponent,
		SettingsUserModalComponent,
		SettingsRoleModalComponent,
		MessagesModalComponent,
		ExecutionVariableModalComponent,
		PlaybookEnvironmentVariableModalComponent
	],
	bootstrap: [MainComponent],
})
export class MainModule {}
