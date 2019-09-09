import { HttpModule, Http, RequestOptions } from '@angular/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, TestBed, ComponentFixture, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import {} from 'jasmine';
import * as moment from 'moment';
import { plainToClass } from 'class-transformer';

import { ExecutionComponent } from './execution.component';
import { ExecutionService } from './execution.service';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { Playbook } from '../models/playbook/playbook';
import { WorkflowStatus } from '../models/execution/workflowStatus';

import { ToastrModule } from 'ngx-toastr';
import { JwtInterceptor, JwtModule } from '@auth0/angular-jwt';
import { RefreshTokenInterceptor, jwtTokenGetter } from '../refresh-token-interceptor';
import { HTTP_INTERCEPTORS } from '@angular/common/http';

describe('ExecutionComponent', () => {
	let comp: ExecutionComponent;
	let fixture: ComponentFixture<ExecutionComponent>;
	let service: ExecutionService;

	const testWorkflowStatuses: WorkflowStatus[] = plainToClass(WorkflowStatus, [
		{
			execution_id: 'wfs-1',
			name: 'Workflow 1',
			workflow_id: 'wf-1',
			status: 'completed',
		},
		{
			execution_id: 'wfs-2',
			name: 'Workflow 2',
			workflow_id: 'wf-2',
			status: 'aborted',
			started_at: moment().subtract(2, 'days').toISOString(),
			completed_at: moment().subtract(1, 'days').toISOString(),
		},
		{
			execution_id: 'wfs-3',
			name: 'Workflow 3',
			workflow_id: 'wf-3',
			status: 'awaiting_data',
			started_at: moment().subtract(1, 'days').toISOString(),
		},
		{
			execution_id: 'wfs-4',
			name: 'Workflow 4',
			workflow_id: 'wf-4',
			status: 'running',
			started_at: moment().toISOString(),
			
		},
		{
			execution_id: 'wfs-5',
			name: 'Workflow 5',
			workflow_id: 'wf-5',
			status: 'paused',
			started_at: moment().subtract(1, 'hours').toISOString(),
		},
		{
			execution_id: 'wfs-6',
			name: 'Workflow 6',
			workflow_id: 'wf-6',
			status: 'queued',
		},
	]);;

	const testPlaybooks: Playbook[] = plainToClass(Playbook, [
		{
			id: 'pb-1',
			name: 'Playbook 1',
			workflows: [
				{
					id: 'wf-1',
					name: 'Workflow 1',
				},
				{
					id: 'wf-2',
					name: 'Workflow 2',
				},
				{
					id: 'wf-3',
					name: 'Workflow 3',
				},
			],
		},
		{
			id: 'pb-2',
			name: 'Playbook 2',
			workflows: [
				{
					id: 'wf-4',
					name: 'Workflow 4',
				},
				{
					id: 'wf-5',
					name: 'Workflow 5',
				},
				{
					id: 'wf-6',
					name: 'Workflow 6',
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
				// NgbModule.forRoot(),
				NgxDatatableModule,
				ToastrModule.forRoot({ positionClass: 'toast-bottom-right' }),
				// FormsModule,
				// ReactiveFormsModule,
			],
			declarations: [ExecutionComponent],
			schemas: [NO_ERRORS_SCHEMA],
			providers: [ExecutionService, JwtInterceptor, 
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
		fixture = TestBed.createComponent(ExecutionComponent);
		comp = fixture.componentInstance;
		service = fixture.debugElement.injector.get(ExecutionService);

		spyOn(window, 'confirm').and.returnValue(true);
		spyOn(service, 'getAllWorkflowStatuses').and.returnValue(Promise.resolve(testWorkflowStatuses));
		spyOn(service, 'getPlaybooks').and.returnValue(Promise.resolve(testPlaybooks));
	});

	// it('should properly display workflow statuses', fakeAsync(() => {
	// 	fixture.detectChanges();
	// 	expect(comp.workflowStatuses).toBeTruthy();
	// 	expect(comp.workflowStatuses.length).toBe(0);
	// 	tick();
	// 	fixture.detectChanges();
	// 	expect(comp.workflowStatuses.length).toBe(testWorkflowStatuses.length);
	// 	const els = fixture.debugElement.queryAll(By.css('.workflowStatusTable .datatable-body-row'));
	// 	expect(els.length).toBe(testWorkflowStatuses.length);
	// }));

	// it('should allow a user to pause a workflow', fakeAsync(() => {
	// 	return false;
	// }));
});
