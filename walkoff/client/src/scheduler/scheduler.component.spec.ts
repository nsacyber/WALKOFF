// import { HttpModule, Http, RequestOptions } from '@angular/http';
// import { NO_ERRORS_SCHEMA } from '@angular/core';
// import { async, TestBed, ComponentFixture, fakeAsync, tick } from '@angular/core/testing';
// import { By } from '@angular/platform-browser';
// import { } from 'jasmine';

// import { SchedulerComponent } from './scheduler.component';
// import { SchedulerService } from './scheduler.service';
// import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
// import { ToastyModule } from 'ng2-toasty';
// import { JwtHttp } from 'angular2-jwt-refresh';
// import { GetJwtHttp } from '../jwthttp.factory';
// import { NgxDatatableModule } from '@swimlane/ngx-datatable';

// describe('SchedulerComponent', () => {
// 	let comp: SchedulerComponent;
// 	let fixture: ComponentFixture<SchedulerComponent>;
// 	let service: SchedulerService;

// 	/**
// 	 * async beforeEach
// 	 */
// 	beforeEach(async(() => {
// 		TestBed.configureTestingModule({
// 			imports: [
// 				HttpModule,
// 				NgbModule.forRoot(),
// 				ToastyModule.forRoot(),
// 				NgxDatatableModule,
// 				// FormsModule,
// 				// ReactiveFormsModule,
// 			],
// 			declarations: [SchedulerComponent],
// 			schemas: [NO_ERRORS_SCHEMA],
// 			providers: [SchedulerService, {
// 				provide: JwtHttp,
// 				useFactory: GetJwtHttp,
// 				deps: [Http, RequestOptions],
// 			}],
// 		})
// 			.compileComponents();
// 	}));

// 	/**
// 	 * Synchronous beforeEach
// 	 */
// 	beforeEach(() => {
// 		fixture = TestBed.createComponent(SchedulerComponent);
// 		comp = fixture.componentInstance;
// 		service = fixture.debugElement.injector.get(SchedulerService);

// 		spyOn(window, 'confirm').and.returnValue(true);
// 		spyOn(service, 'getScheduledTasks').and.returnValue(Promise.resolve(testScheduledTasks));
// 		spyOn(service, 'getPlaybooks').and.returnValue(Promise.resolve(testPlaybooks));
// 		spyOn(service, 'deleteScheduledTask').and.returnValue(Promise.resolve());
// 	});
// 	it('should properly display scheduled items', fakeAsync(() => {
// 		fixture.detectChanges();
// 		expect(comp.scheduledTasks).toBeTruthy();
// 		expect(comp.scheduledTasks.length).toBe(0);
// 		tick();
// 		fixture.detectChanges();
// 		expect(comp.scheduledTasks.length).toBe(testScheduledTasks.length);
// 		const els = fixture.debugElement.queryAll(By.css('.scheduledTasksTable .datatable-body-row'));
// 		expect(els.length).toBe(testScheduledTasks.length);
// 	}));

// 	it('should properly remove scheduled item from the display on delete', fakeAsync(() => {
// 		fixture.detectChanges();
// 		tick();
// 		fixture.detectChanges();
// 		const originalCount = testScheduledTasks.length;
// 		expect(comp.scheduledTasks.length).toBe(originalCount);
// 		let els = fixture.debugElement.queryAll(By.css('.scheduledTasksTable .datatable-body-row'));
// 		expect(els.length).toBe(originalCount);

// 		comp.deleteScheduledTask(comp.scheduledTasks[0]);
// 		tick();
// 		fixture.detectChanges();
// 		expect(comp.scheduledTasks.length).toBe(originalCount - 1);
// 		els = fixture.debugElement.queryAll(By.css('.scheduledTasksTable .datatable-body-row'));
// 		expect(els.length).toBe(originalCount - 1);
// 	}));
// });
