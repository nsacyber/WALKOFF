import { NgModule } from '@angular/core';
import { Http, RequestOptions, Response } from '@angular/http';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule }   from '@angular/forms';
import { HttpModule } from '@angular/http';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { ToastyModule } from 'ng2-toasty';
import { Select2Module } from 'ng2-select2';
import { AuthConfig, tokenNotExpired } from 'angular2-jwt';
import { JwtConfigService, JwtHttp, RefreshConfig } from 'angular2-jwt-refresh';
import { DateTimePickerModule } from 'ng-pick-datetime';
import { DndModule } from 'ng2-dnd';

// Custom routing module
import { RoutingModule } from './routing';
import { MainComponent } from './main/main.component';
import { SchedulerComponent } from './scheduler/scheduler.component';
import { PlaybookComponent } from './playbook/playbook.component';
import { DevicesComponent } from './devices/devices.component';
// import { TriggersComponent } from './triggers/triggers.component';
import { CasesComponent } from './cases/cases.component';
import { SettingsComponent } from './settings/settings.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { AppsComponent } from './apps/apps.component';

import { SchedulerModalComponent } from './scheduler/scheduler.modal.component';
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
		DateTimePickerModule,
		DndModule.forRoot()
	],
	declarations: [
		//Main component
		MainComponent,
		//Router module components
		PlaybookComponent,
		DashboardComponent,
		SchedulerComponent,
		DevicesComponent,
		// TriggersComponent,
		CasesComponent,
		SettingsComponent,
		AppsComponent,
		//Modals
		SchedulerModalComponent,
		DevicesModalComponent,
		CasesModalComponent,
		SettingsUserModalComponent,
	],
	providers: [{
		provide: JwtHttp,
		useFactory: getJwtHttp,
		deps: [ Http, RequestOptions ]
	}],
	entryComponents: [
		SchedulerModalComponent,
		DevicesModalComponent,
		CasesModalComponent,
		SettingsUserModalComponent,
	],
	bootstrap: [MainComponent]
})
export class MainModule {}

export function getJwtHttp(http: Http, options: RequestOptions) {
	let jwtOptions: RefreshConfig = {
		endPoint: '/api/auth/refresh',
		// optional
		// payload: { type: 'refresh' },
		beforeSeconds: 300, // refresh token before 5 min
		tokenName: 'refresh_token',
		refreshTokenGetter: (() => {
			let token = sessionStorage.getItem('refresh_token');

			if (token && tokenNotExpired(null, token)) return token;

			//TODO: figure out a better way of handling this... maybe incorporate login into the main component somehow
			location.href = '/login';
			return;
		}),
		tokenSetter: ((res: Response): boolean | Promise<void> => {
			res = res.json();

			if (!(<any>res)['access_token']) {
				sessionStorage.removeItem('access_token');
				sessionStorage.removeItem('refresh_token');
				//TODO: figure out a better way of handling this... maybe incorporate login into the main component somehow
				location.href = '/login';
				return false;
			}

			sessionStorage.setItem('access_token', (<any>res)['access_token']);
			// sessionStorage.setItem('refresh_token', (<any>res)['refresh_token']);

			return true;
		})
	};

	let authConfig = new AuthConfig({
		noJwtError: true,
		// globalHeaders: [{ 'Accept': 'application/json' }],
		tokenName: 'access_token',
		tokenGetter: (() => sessionStorage.getItem('access_token')),
	});

	return new JwtHttp(
		new JwtConfigService(jwtOptions, authConfig),
		http,
		options
	);
}
