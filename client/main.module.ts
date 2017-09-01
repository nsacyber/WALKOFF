import { NgModule } from '@angular/core';
import { Http, RequestOptions, Response } from '@angular/http';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule }   from '@angular/forms';
import { HttpModule } from '@angular/http';
// import { DataTableModule } from 'angular2-datatable';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { ToastyModule } from 'ng2-toasty';
import { Select2Module } from 'ng2-select2';
// import { ContextMenuModule } from 'ngx-contextmenu';
import { AuthConfig, tokenNotExpired } from 'angular2-jwt';
import { JwtConfigService, JwtHttp, RefreshConfig } from 'angular2-jwt-refresh';

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
	providers: [{
		provide: JwtHttp,
		useFactory: getJwtHttp,
		deps: [ Http, RequestOptions ]
	}],
	entryComponents: [
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
			let token = localStorage.getItem('refresh_token');

			if (token && tokenNotExpired(null, token)) return token;

			//TODO: figure out a better way of handling this... maybe incorporate login into the main component somehow
			location.href = '/login';
			return;
		}),
		tokenSetter: ((res: Response): boolean | Promise<void> => {
			res = res.json();

			if (!(<any>res)['access_token']) {
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');
				//TODO: figure out a better way of handling this... maybe incorporate login into the main component somehow
				location.href = '/login';
				return false;
			}

			localStorage.setItem('access_token', (<any>res)['access_token']);
			// localStorage.setItem('refresh_token', (<any>res)['refresh_token']);

			return true;
		})
	};

	let authConfig = new AuthConfig({
		noJwtError: true,
		// globalHeaders: [{ 'Accept': 'application/json' }],
		tokenName: 'access_token',
		tokenGetter: (() => localStorage.getItem('access_token')),
	});

	return new JwtHttp(
		new JwtConfigService(jwtOptions, authConfig),
		http,
		options
	);
}