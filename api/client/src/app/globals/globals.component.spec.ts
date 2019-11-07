import { HttpModule, Http, RequestOptions } from '@angular/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, TestBed, ComponentFixture, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { plainToClass } from 'class-transformer';
import {} from 'jasmine';

import { GlobalsComponent } from './globals.component';
import { GlobalsService } from './globals.service';
import { Global } from '../models/global';
import { AppApi } from '../models/api/appApi';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';

import { ToastrModule } from 'ngx-toastr';
import { JwtInterceptor, JwtModule } from '@auth0/angular-jwt';
import { RefreshTokenInterceptor, jwtTokenGetter } from '../refresh-token-interceptor';
import { HTTP_INTERCEPTORS } from '@angular/common/http';

describe('GlobalsComponent', () => {
	let comp: GlobalsComponent;
	let fixture: ComponentFixture<GlobalsComponent>;
	let service: GlobalsService;

	const testGlobalApis: AppApi[] = plainToClass(AppApi, [
		{
			name: 'app_name',
			global_apis: [
				{
					name: 'type',
					description: 'description',
					fields: [
						{
							name: 'text field',
							description: 'text field',
							schema: {
								type: 'string',
							},
						},
						{
							name: 'number field',
							schema: {
								type: 'integer',
							},
						},
						{
							name: 'boolean field',
							schema: {
								type: 'integer',
							},
						},
					],
				},
			],
		},
	]);

	const testGlobals: Global[] = plainToClass(Global, [
		{
			id: 1,
			name: 'name',
			description: 'description',
			type: 'type',
			app_name: 'app_name',
			fields: [
				{
					name: 'text field',
					value: 'hello',
				},
				{
					name: 'number field',
					value: 5,
				},
				{
					name: 'boolean field',
					value: true,
				},
			],
		},
	]);

	/**
	 * async beforeEach
	 */
	beforeEach(async(() => {
		TestBed.configureTestingModule({
			imports: [
				HttpModule,
				NgbModule.forRoot(),
				NgxDatatableModule,
				JwtModule.forRoot({
					config: {
						tokenGetter: jwtTokenGetter,
						blacklistedRoutes: ['login', 'api/auth/login', 'api/auth/logout', 'api/auth/refresh']
					}
				}),
				ToastrModule.forRoot({ positionClass: 'toast-bottom-right' })
				// FormsModule,
				// ReactiveFormsModule,
			],
			declarations: [GlobalsComponent],
			schemas: [NO_ERRORS_SCHEMA],
			providers: [GlobalsService, JwtInterceptor,
			// Providing JwtInterceptor allow to inject JwtInterceptor manually into RefreshTokenInterceptor
			{
				provide: HTTP_INTERCEPTORS,
				useExisting: JwtInterceptor,
				multi: true
			},
			{
				provide: HTTP_INTERCEPTORS,
				useClass: RefreshTokenInterceptor,
				multi: true
			}],
		})
		.compileComponents();
	}));

	/**
	 * Synchronous beforeEach
	 */
	beforeEach(() => {
		fixture = TestBed.createComponent(GlobalsComponent);
		comp = fixture.componentInstance;
		service = fixture.debugElement.injector.get(GlobalsService);

		spyOn(window, 'confirm').and.returnValue(true);
		spyOn(service, 'getAllGlobals').and.returnValue(Promise.resolve(testGlobals));
		spyOn(service, 'getGlobalApis').and.returnValue(Promise.resolve(testGlobalApis));
		spyOn(service, 'deleteGlobal').and.returnValue(Promise.resolve());
	});

	// it('should properly display globals', fakeAsync(() => {
	// 	fixture.detectChanges();
	// 	expect(comp.globals).toBeTruthy();
	// 	expect(comp.globals.length).toBe(0);
	// 	tick();
	// 	fixture.detectChanges();
	// 	expect(comp.globals.length).toBe(testGlobals.length);
	// 	const els = fixture.debugElement.queryAll(By.css('.datatable-body-row'));
	// 	expect(els.length).toBe(testGlobals.length);
	// }));

	// it('should properly remove global from the display on delete', fakeAsync(() => {
	// 	fixture.detectChanges();
	// 	tick();
	// 	fixture.detectChanges();
	// 	const originalCount = testGlobals.length;
	// 	expect(comp.globals.length).toBe(originalCount);
	// 	let els = fixture.debugElement.queryAll(By.css('.datatable-body-row'));
	// 	expect(els.length).toBe(originalCount);

	// 	comp.deleteGlobal(comp.globals[0]);
	// 	tick();
	// 	fixture.detectChanges();
	// 	expect(comp.globals.length).toBe(originalCount - 1);
	// 	els = fixture.debugElement.queryAll(By.css('.datatable-body-row'));
	// 	expect(els.length).toBe(originalCount - 1);
	// }));

	// it('should properly open a modal on clicking add global', fakeAsync(() => {
	// 	fixture.detectChanges();
	// 	tick();
	// 	fixture.detectChanges();
	// 	comp.addGlobal();
	// }));
});
