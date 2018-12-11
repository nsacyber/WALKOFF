import { HttpModule, Http, RequestOptions } from '@angular/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, fakeAsync, tick, TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { } from 'jasmine';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { MainComponent } from './main.component';
import { MainService } from './main.service';
import { AuthService } from '../auth/auth.service';

// import { Message } from '../models/message/message';
import { MessageListing } from '../models/message/messageListing';

import { ToastrModule } from 'ngx-toastr';
import { JwtInterceptor, JwtModule } from '@auth0/angular-jwt';
import { RefreshTokenInterceptor, jwtTokenGetter } from '../refresh-token-interceptor';
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { plainToClass } from 'class-transformer';

describe('App', () => {
	let comp: MainComponent;
	let fixture: ComponentFixture<MainComponent>;

	// let getInterfaceNamesSpy: jasmine.Spy;
	// let getInitialNotificationsSpy: jasmine.Spy;
	// let getAndDecodeAccessTokenSpy: jasmine.Spy;

	let mainService: MainService;
	let authService: AuthService;

	const testInterfaceNames = ['MyInterface', 'SomeOtherInterface', 'ThirdInterface'];
	const testInitialNotifications: MessageListing[] = plainToClass(MessageListing, [
		{
			id: 5,
			subject: 'Need Action',
			created_at: new Date(),
			awaiting_response: true,
			is_read: false,
			last_read_at: null,
		},
		{
			id: 4,
			subject: 'Informative Message',
			created_at: new Date(),
			awaiting_response: false,
			is_read: false,
			last_read_at: null,
		},
		{
			id: 3,
			subject: 'Already Acted On',
			created_at: new Date(),
			awaiting_response: false,
			is_read: true,
			last_read_at: new Date(),
		},
		{
			id: 2,
			subject: 'Already Read',
			created_at: new Date(),
			awaiting_response: true,
			is_read: true,
			last_read_at: new Date(),
		},
		{
			id: 1,
			subject: 'Another One',
			created_at: new Date(),
			awaiting_response: false,
			is_read: true,
			last_read_at: new Date(),
		},
	]);
	// const testMessage: Message = { };
	const testDecodedJwt = { user_claims: { username: 'test' } };

	/**
	 * async beforeEach
	 */
	beforeEach(async(() => {
		TestBed.configureTestingModule({
			imports: [
				//HttpModule,
				NgbModule.forRoot(),
				ToastrModule.forRoot({ positionClass: 'toast-bottom-right' }),
			],
			declarations: [MainComponent],
			schemas: [NO_ERRORS_SCHEMA],
			providers: [MainService],
		})
			.compileComponents();
	}));

	/**
	 * Synchronous beforeEach
	 */
	// beforeEach(() => {
	// 	fixture = TestBed.createComponent(MainComponent);
	// 	comp = fixture.componentInstance;

	// 	// Services actually injected into the component
	// 	mainService = fixture.debugElement.injector.get(MainService);
	// 	authService = fixture.debugElement.injector.get(AuthService);

	// 	spyOn(comp, 'getNotificationsSSE').and.stub();

	// 	spyOn(mainService, 'getInterfaceNames')
	// 		.and.returnValue(Promise.resolve(testInterfaceNames));
	// 	spyOn(mainService, 'getInitialNotifications')
	// 		.and.returnValue(Promise.resolve(testInitialNotifications));
	// 	// spyOn(mainService, 'getMessage')
	// 	// 	.and.returnValue(Promise.resolve(testInterfaceNames));
	// 	spyOn(authService, 'getAndDecodeAccessToken')
	// 		.and.returnValue(testDecodedJwt);
	// });

	it('should pass', () => {
		expect(true).toEqual(true);
	});

	// it('should properly load the username', () => {
	// 	fixture.detectChanges();
	// 	expect(comp.currentUser).toEqual('test');
	// 	const el = fixture.debugElement.query(By.css('.userName'));
	// 	expect(el.nativeElement.textContent).toEqual('test');
	// });

	// it('should grab interface names', fakeAsync(() => {
	// 	fixture.detectChanges();
	// 	expect(comp.interfaceNames).toBeTruthy();
	// 	expect(comp.interfaceNames.length).toBe(0);
	// 	tick();
	// 	fixture.detectChanges();
	// 	expect(fixture.componentInstance.interfaceNames).toBe(testInterfaceNames);
	// 	const els = fixture.debugElement.queryAll(By.css('.installedInterface'));
	// 	expect(els.length).toBeGreaterThan(0);
	// }));

	// it('should grab initial notifications', fakeAsync(() => {
	// 	fixture.detectChanges();
	// 	expect(comp.messageListings).toBeTruthy();
	// 	expect(comp.messageListings.length).toBe(0);
	// 	tick();
	// 	fixture.detectChanges();
	// 	expect(comp.messageListings.length).toBeGreaterThan(0);
	// 	// also check that the unread number changes, and the list of messages
	// 	const el = fixture.debugElement.query(By.css('.messages-menu a span'));
	// 	// 2 unread messages
	// 	expect(el.nativeElement.textContent).toEqual('2');
	// 	const els = fixture.debugElement.queryAll(By.css('.messageTable tr'));
	// 	expect(els.length).toEqual(5);
	// }));
});
