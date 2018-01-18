import { HttpModule, Http, RequestOptions } from '@angular/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, TestBed, ComponentFixture, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { } from 'jasmine';

import { SchedulerComponent } from './scheduler.component';
import { SchedulerService } from './scheduler.service';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { ToastyModule } from 'ng2-toasty';
import { JwtHttp } from 'angular2-jwt-refresh';
import { GetJwtHttp } from '../jwthttp.factory';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { SchedulerModalComponent } from './scheduler.modal.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { Case } from '../models/case';
import { AvailableSubscription } from '../models/availableSubscription';
import { Playbook } from '../models/playbook/playbook';

fdescribe('SchedulerComponent', () => {
	let comp: SchedulerComponent;
	let fixture: ComponentFixture<SchedulerComponent>;
	let service: SchedulerService;

	const testCases: Case[] = [
		{
			id: 1,
			name: 'case 1',
			note: 'something',
			subscriptions: [
				{
					uid: '12345',
					events: ['some', 'events', 'go', 'here'],
				},
			],
		},
	];

	const testAvailableSubscriptions: AvailableSubscription[] = [
		{
			events: [
				'Job Added',
				'Job Error',
				'Job Executed',
				'Job Removed',
				'Scheduler Paused',
				'Scheduler Resumed',
				'Scheduler Shutdown',
				'Scheduler Start',
			],
			type: 'controller',
		},
		{
			events: [],
			type: 'playbook',
		},
		{
			events: [
				'App Instance Created',
				'Workflow Arguments Invalid',
				'Workflow Arguments Validated',
				'Workflow Execution Start',
				'Workflow Paused',
				'Workflow Resumed',
				'Workflow Shutdown',
			],
			type: 'workflow',
		},
		{
			events: [
				'Action Execution Error',
				'Action Execution Success',
				'Action Started',
				'Arguments Invalid',
				'Trigger Action Awaiting Data',
				'Trigger Action Not Taken',
				'Trigger Action Taken',
			],
			type: 'action',
		},
		{
			events: [
				'Branch Not Taken',
				'Branch Taken',
			],
			type: 'branch',
		},
		{
			events: [
				'Condition Error',
				'Condition Success',
			],
			type: 'condition',
		},
		{
			events: [
				'Transform Error',
				'Transform Success',
			],
			type: 'transform',
		},
	];

	const testPlaybooks: Playbook[] = [
		{
			uid: 'pb-12345',
			name: 'test playbook',
			workflows: [
				{
					uid: 'wf-12345',
					name: 'TestWorkflow',
					actions: [
						{
							uid: 'ac-12345',
							name: 'test action',
							position: { x: 0, y: 0 },
							app_name: 'TestApp',
							action_name: 'TestActon',
							arguments: [
								{
									name: 'test',
									value: 'value',
								},
							],
							triggers: [],
						},
					],
					branches: [],
					start: 'ac-12345',
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
			declarations: [SchedulerComponent],
			schemas: [NO_ERRORS_SCHEMA],
			providers: [SchedulerService, {
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
		fixture = TestBed.createComponent(SchedulerComponent);
		comp = fixture.componentInstance;
		service = fixture.debugElement.injector.get(SchedulerService);

		spyOn(window, 'confirm').and.returnValue(true);
		spyOn(service, 'getScheduledTasks').and.returnValue(Promise.resolve(testCases));
		spyOn(service, 'getPlaybooks').and.returnValue(Promise.resolve(testPlaybooks));
		spyOn(service, 'deleteScheduledTask').and.returnValue(Promise.resolve());
	});

	it('should properly display scheduled items', fakeAsync(() => {
		fixture.detectChanges();
		expect(comp.cases).toBeTruthy();
		expect(comp.cases.length).toBe(0);
		tick();
		fixture.detectChanges();
		expect(comp.cases.length).toBe(testCases.length);
		const els = fixture.debugElement.queryAll(By.css('.casesTable .datatable-body-row'));
		expect(els.length).toBe(testCases.length);
	}));

	it('should properly remove scheduled item from the display on delete', fakeAsync(() => {
		fixture.detectChanges();
		tick();
		fixture.detectChanges();
		const originalCount = testCases.length;
		expect(comp.cases.length).toBe(originalCount);
		let els = fixture.debugElement.queryAll(By.css('.casesTable .datatable-body-row'));
		expect(els.length).toBe(originalCount);

		comp.deleteCase(comp.cases[0]);
		tick();
		fixture.detectChanges();
		expect(comp.cases.length).toBe(originalCount - 1);
		els = fixture.debugElement.queryAll(By.css('.casesTable .datatable-body-row'));
		expect(els.length).toBe(originalCount - 1);
	}));

});
