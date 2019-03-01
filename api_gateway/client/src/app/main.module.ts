import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { Select2Module } from 'ng2-select2';
import { AuthService } from './auth/auth.service';
import { JwtInterceptor, JwtModule } from '@auth0/angular-jwt';
import { RefreshTokenInterceptor, jwtTokenGetter } from './refresh-token-interceptor';
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import { DateTimePickerModule } from 'ng-pick-datetime';
import { DndModule } from 'ng2-dnd';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ToastrModule } from 'ngx-toastr';
import { GridsterModule } from 'angular-gridster2';
import { ChartsModule } from 'ng2-charts';
import { CodemirrorModule } from '@ctrl/ngx-codemirror';
import 'codemirror/mode/shell/shell';

// Custom routing module
import { RoutingModule } from './routing';
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
import { SettingsTimeoutModalComponent } from './settings/settings.timeout.modal.component';
import { ExecutionVariableModalComponent } from './execution/execution.variable.modal.component';
import { PlaybookEnvironmentVariableModalComponent } from './playbook/playbook.environment.variable.modal.component';

import { PlaybookArgumentComponent } from './playbook/playbook.argument.component';
import { PlaybookConditionsComponent } from './playbook/playbook.conditions.component';
import { PlaybookTransformsComponent } from './playbook/playbook.transforms.component';
import { PlaybookConditionalExpressionComponent } from './playbook/playbook.conditional.expression.component';
import { SettingsRolesComponent } from './settings/settings.roles.component';
import { MessagesModalComponent } from './messages/messages.modal.component';

import { KeysPipe } from './pipes/keys.pipe';
import { UtilitiesService } from './utilities.service';
import { ManageInterfacesComponent } from './interfaces/manage.interfaces.component';
import { WidgetModalComponent } from './interfaces/widget.modal.component';

@NgModule({
	imports: [
		BrowserModule,
		FormsModule,
		ReactiveFormsModule,
		HttpClientModule,
		JwtModule.forRoot({
			config: {
				tokenGetter: jwtTokenGetter,
				blacklistedRoutes: ['/login', '/api/auth', '/api/auth/logout', '/api/auth/refresh']
			}
		}),
		RoutingModule,
		NgbModule,
		NgxDatatableModule,
		Select2Module,
		DateTimePickerModule,
		DndModule.forRoot(),
	    BrowserAnimationsModule,
		ToastrModule.forRoot({ positionClass: 'toast-bottom-right' }),
		GridsterModule,
		ChartsModule,
		CodemirrorModule
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
		SettingsTimeoutModalComponent,
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
		ManageInterfacesComponent,
		WidgetModalComponent,
	],
	providers: [
		UtilitiesService,
		AuthService,
		JwtInterceptor, // Providing JwtInterceptor allow to inject JwtInterceptor manually into RefreshTokenInterceptor
		{
			provide: HTTP_INTERCEPTORS,
			useExisting: JwtInterceptor,
			multi: true
		},
		{
			provide: HTTP_INTERCEPTORS,
			useClass: RefreshTokenInterceptor,
			multi: true
		}
	],
	entryComponents: [
		SchedulerModalComponent,
		DevicesModalComponent,
		SettingsUserModalComponent,
		SettingsRoleModalComponent,
		SettingsTimeoutModalComponent,
		MessagesModalComponent,
		ExecutionVariableModalComponent,
		PlaybookEnvironmentVariableModalComponent,
		WidgetModalComponent
	],
	bootstrap: [MainComponent],
})
export class MainModule {}
