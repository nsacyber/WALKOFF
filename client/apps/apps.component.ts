import { Component, OnInit, ElementRef, ViewChild, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Observable } from 'rxjs/Observable';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';

import { AuthService } from '../auth/auth.service';

function makeComponent(selector: string, templateUrl: string)
{
	@Component({ selector: selector, templateUrl: templateUrl })
	class FakeComponent {}
	return FakeComponent;
}

@Component({
	selector: 'apps-component',
	templateUrl: 'client/apps/apps.html',
	styleUrls: ['client/apps/apps.css'],
	encapsulation: ViewEncapsulation.None,
	providers: [AuthService]
})
export class AppsComponent {
	@ViewChild('appsMain') main: ElementRef;
	appName: string;
	paramsSub: any;
	activeIFrame: any;

	constructor(private route: ActivatedRoute, private authService: AuthService, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';
	}

	ngOnInit() {
		this.paramsSub = this.route.params.subscribe(params => {
			this.appName = params['app'];
			this.getAppInterface();
		});
	}

	getAppInterface() {
		let self = this;

		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				var xhr= new XMLHttpRequest();
				xhr.open('GET', `apps/${this.appName}/`, true);
				xhr.onreadystatechange= function() {
					if (this.readyState!==4) return;
					if (this.status!==200) return;

					//Remove our existing iframe if applicable
					self.main.nativeElement.removeChild(self.main.nativeElement.lastChild);

					self.activeIFrame = document.createElement('iframe');
					(<any>self.activeIFrame).srcdoc = this.responseText;
					self.activeIFrame.src = "data:text/html;charset=utf-8," + this.responseText;

					self.main.nativeElement.appendChild(self.activeIFrame);
				};
				xhr.setRequestHeader('Authorization', 'Bearer ' + authToken);
				xhr.send();
			})
			.catch(e => this.toastyService.error(`Error retrieving app: ${e.message}`));
	}
}