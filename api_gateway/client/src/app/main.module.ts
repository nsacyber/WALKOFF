import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { Select2Module } from 'ng2-select2';
import { ClipboardModule } from 'ngx-clipboard';
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

import { NgJsonEditorModule } from 'ang-jsoneditor' 

import { CodemirrorModule } from '@ctrl/ngx-codemirror';
import 'codemirror/mode/shell/shell';
import 'codemirror/mode/python/python';
import 'codemirror/addon/display/placeholder';

// Custom routing module
import { RoutingModule } from './routing';
import { MainComponent } from './main/main.component';
import { SchedulerComponent } from './scheduler/scheduler.component';
import { PlaybookComponent } from './playbook/playbook.component';
import { GlobalsComponent } from './globals/globals.component';
import { MessagesComponent } from './messages/messages.component';
import { MetricsComponent } from './metrics/metrics.component';
import { SettingsComponent } from './settings/settings.component';
import { DashboardsComponent } from './dashboards/dashboards.component';
import { ExecutionComponent } from './execution/execution.component';
import { BucketsComponent } from './buckets/buckets.component';
import { TriggersModalComponent } from './buckets/triggers.modal.component';
import { SchedulerModalComponent } from './scheduler/scheduler.modal.component';
import { GlobalsModalComponent } from './globals/globals.modal.component';
import { BucketsModalComponent } from './buckets/buckets.modal.component';
import { VariableModalComponent } from './globals/variable.modal.component';
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
import { ManageDashboardsComponent } from './dashboards/manage.dashboards.component';
import { WidgetModalComponent } from './dashboards/widget.modal.component';
import { SafeEmbedPipe } from './pipes/safeEmbed.pipe';
import { WorkflowEditorComponent } from './playbook/workflow.editor.component';
import { MetadataModalComponent } from './playbook/metadata.modal.component';
import { ImportModalComponent } from './playbook/import.modal.component';

import { Bucket } from './models/buckets/bucket';

@NgModule({
	imports: [
		FormsModule,
		BrowserModule,
		HttpClientModule,
		ReactiveFormsModule,
		JwtModule.forRoot({
			config: {
				tokenGetter: jwtTokenGetter,
				blacklistedRoutes: ['/login', '/api/auth', '/api/auth/logout', '/api/auth/refresh']
			}
		}),
		NgbModule,
		RoutingModule,
		Select2Module,
		ClipboardModule,
		NgxDatatableModule,
		DateTimePickerModule,
		DndModule.forRoot(),
	    BrowserAnimationsModule,
		ToastrModule.forRoot({ positionClass: 'toast-bottom-right', enableHtml: true, onActivateTick: true }),
		GridsterModule,
		ChartsModule,
		CodemirrorModule,
		NgJsonEditorModule
	],
	declarations: [
		//Main component
		MainComponent,
		//Router module components
		PlaybookComponent,
		WorkflowEditorComponent,
		SchedulerComponent,
		GlobalsComponent,
		MessagesComponent,
		MetricsComponent,
		SettingsComponent,
		DashboardsComponent,
		ExecutionComponent,
		BucketsComponent,
		//Modals
		SchedulerModalComponent,
		GlobalsModalComponent,
		BucketsModalComponent,
		VariableModalComponent,
		SettingsUserModalComponent,
		SettingsRoleModalComponent,
		SettingsTimeoutModalComponent,
		MessagesModalComponent,
		PlaybookEnvironmentVariableModalComponent,
		MetadataModalComponent,
		ImportModalComponent,
		ExecutionVariableModalComponent,
		TriggersModalComponent,
		// Other subcomponents
		PlaybookArgumentComponent,
		PlaybookConditionsComponent,
		PlaybookTransformsComponent,
		PlaybookConditionalExpressionComponent,
		SettingsRolesComponent,
		// Pipes
		KeysPipe,
		ManageDashboardsComponent,
		SafeEmbedPipe,
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
		GlobalsModalComponent,
		VariableModalComponent,
		BucketsModalComponent,
		TriggersModalComponent,
		SettingsUserModalComponent,
		SettingsRoleModalComponent,
		SettingsTimeoutModalComponent,
		MessagesModalComponent,
		ExecutionVariableModalComponent,
		PlaybookEnvironmentVariableModalComponent,
		ImportModalComponent,
		MetadataModalComponent,
		WidgetModalComponent
	],
	bootstrap: [MainComponent],
})
export class MainModule {}
