import { HttpModule, Http, RequestOptions } from '@angular/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, TestBed, ComponentFixture, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import {} from 'jasmine';

import { DevicesComponent } from './devices.component';
import { DevicesService } from './devices.service';
import { Device } from '../models/device';
import { AppApi } from '../models/api/appApi';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { ToastyModule } from 'ng2-toasty';
import { JwtHttp } from 'angular2-jwt-refresh';
import { GetJwtHttp } from '../jwthttp.factory';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';

describe('DevicesComponent', () => {
	let comp: DevicesComponent;
	let fixture: ComponentFixture<DevicesComponent>;
	let service: DevicesService;

	const testDeviceApis: AppApi[] = [
		{
			name: 'app_name',
			device_apis: [
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
	];
	const testDevices: Device[] = [
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
	];
	/**
	 * async beforeEach
	 */
	beforeEach(async(() => {
		TestBed.configureTestingModule({
			imports: [
				HttpModule,
				NgbModule.forRoot(),
				ToastyModule.forRoot(),
				NgxDatatableModule,
				// FormsModule,
				// ReactiveFormsModule,
			],
			declarations: [DevicesComponent],
			schemas: [NO_ERRORS_SCHEMA],
			providers: [DevicesService, {
				provide: JwtHttp,
				useFactory: GetJwtHttp,
				deps: [Http, RequestOptions],
			}],
		})
			.compileComponents();
	}));

	/**
	 * Synchronous beforeEach
	 */
	beforeEach(() => {
		fixture = TestBed.createComponent(DevicesComponent);
		comp = fixture.componentInstance;
		service = fixture.debugElement.injector.get(DevicesService);

		spyOn(window, 'confirm').and.returnValue(true);
		spyOn(service, 'getDevices').and.returnValue(Promise.resolve(testDevices));
		spyOn(service, 'getDeviceApis').and.returnValue(Promise.resolve(testDeviceApis));
		spyOn(service, 'deleteDevice').and.returnValue(Promise.resolve());
	});

	it('should properly display devices', fakeAsync(() => {
		fixture.detectChanges();
		expect(comp.devices).toBeTruthy();
		expect(comp.devices.length).toBe(0);
		tick();
		fixture.detectChanges();
		expect(comp.devices.length).toBe(testDevices.length);
		const els = fixture.debugElement.queryAll(By.css('.datatable-body-row'));
		expect(els.length).toBe(testDevices.length);
	}));

	it('should properly remove device from the display on delete', fakeAsync(() => {
		fixture.detectChanges();
		tick();
		fixture.detectChanges();
		const originalCount = testDevices.length;
		expect(comp.devices.length).toBe(originalCount);
		let els = fixture.debugElement.queryAll(By.css('.datatable-body-row'));
		expect(els.length).toBe(originalCount);

		comp.deleteDevice(comp.devices[0]);
		tick();
		fixture.detectChanges();
		expect(comp.devices.length).toBe(originalCount - 1);
		els = fixture.debugElement.queryAll(By.css('.datatable-body-row'));
		expect(els.length).toBe(originalCount - 1);
	}));

	// it('should properly open a modal on clicking add device', fakeAsync(() => {
	// 	fixture.detectChanges();
	// 	tick();
	// 	fixture.detectChanges();
	// 	comp.addDevice();
	// }));
});
