import { Component, ElementRef, ViewChild, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ToastyService, ToastyConfig } from 'ng2-toasty';

import { AuthService } from '../auth/auth.service';

@Component({
	selector: 'apps-component',
	templateUrl: 'client/apps/apps.html',
	styleUrls: ['client/apps/apps.css'],
	encapsulation: ViewEncapsulation.None,
	providers: [AuthService],
})
export class AppsComponent {
	@ViewChild('appsMain') main: ElementRef;
	appName: string;
	paramsSub: any;
	activeIFrame: any;

	constructor(
		private route: ActivatedRoute, private authService: AuthService,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';
	}

	ngOnInit() {
		this.paramsSub = this.route.params.subscribe(params => {
			this.appName = params.app;
			this.getAppInterface();
		});
	}

	getAppInterface() {
		const self = this;

		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const xhr = new XMLHttpRequest();
				xhr.open('GET', `appinterface/${this.appName}/`, true);
				xhr.onreadystatechange = function() {
					if (this.readyState !== 4) {
						return;
					}
					if (this.status !== 200) {
						return;
					}

					//Remove our existing iframe if applicable
					self.main.nativeElement.removeChild(self.main.nativeElement.lastChild);

					self.activeIFrame = document.createElement('iframe');
					(self.activeIFrame as any).srcdoc = this.responseText;
					self.activeIFrame.src = 'data:text/html;charset=utf-8,' + this.responseText;

					self.main.nativeElement.appendChild(self.activeIFrame);
				};
				xhr.setRequestHeader('Authorization', 'Bearer ' + authToken);
				xhr.send();
			})
			.catch(e => this.toastyService.error(`Error retrieving app: ${e.message}`));
	}
}

// function makeComponent(_selector: string, _templateUrl: string) {
// 	// tslint:disable-next-line:max-classes-per-file
// 	@Component({ selector: _selector, templateUrl: _templateUrl })
// 	class FakeComponent {}
// 	return FakeComponent;
// }
