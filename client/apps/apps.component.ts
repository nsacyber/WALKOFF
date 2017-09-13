import { Component, ComponentRef, Input, OnInit, ViewContainerRef, ElementRef, ViewChild, ComponentFactoryResolver, OnDestroy, ViewEncapsulation } from '@angular/core';
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
	// @ViewChild('viewChild', {read: ViewContainerRef}) viewChild: ViewContainerRef;
	// componentRef: ComponentRef<{}>;
	appName: string;
	paramsSub: any;
	activeIFrame: any;

	constructor(private route: ActivatedRoute, private authService: AuthService, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {}

	ngOnInit() {
		this.paramsSub = this.route.params.subscribe(params => {
			this.appName = params['app'];
			this.getAppInterface();
		});

		//Resize our iframe as necessary
		window.addEventListener('DOMContentLoaded', function(e) {
			let iFrame = this.main.nativeRef.lastChild;
			iFrame.height = iFrame.contentWindow.document.body.scrollHeight;
		});
	}

	loadComponent() {
		
		// let childComponent = makeComponent(`${this.appName}-app`, `apps/${this.appName}/interface/index.html`);
	
		// let componentFactory = this.componentFactoryResolver.resolveComponentFactory(childComponent);

		// // compile then insert in your location, defined by viewChild
		// // this.compiler.resolveComponent()
		// //   .then((compFactory:ComponentFactory) => this.viewChild.createComponent(compFactory) )
		
		// // let viewContainerRef = this.appsHost.viewContainerRef;
		// this.viewChild.clear();
		
		// this.componentRef = this.viewChild.createComponent(componentFactory);
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