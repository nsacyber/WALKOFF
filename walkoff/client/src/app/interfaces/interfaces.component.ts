import { Component, ElementRef, ViewChild, ViewEncapsulation, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ToastrService } from 'ngx-toastr';

import { AuthService } from '../auth/auth.service';
import { HttpClient } from '@angular/common/http';

@Component({
	selector: 'interfaces-component',
	templateUrl: './interfaces.html',
	styleUrls: ['./interfaces.scss'],
	encapsulation: ViewEncapsulation.None,
	providers: [AuthService],
})
export class InterfacesComponent implements OnInit {
	@ViewChild('interfacesMain') main: ElementRef;
	interfaceName: string;
	paramsSub: any;
	activeIFrame: any;

	constructor(
		private route: ActivatedRoute, private toastrService: ToastrService, private http: HttpClient
	) {}

	/**
	 * On init, get our interface name from the route params and grab the interface.
	 */
	ngOnInit() {
		this.paramsSub = this.route.params.subscribe(params => {
			this.interfaceName = params.interfaceName;
			this.getInterface();
		});
	}

	/**
	 * Gets the interface by the name specified in the route params.
	 * Loads the interface into an iframe currently.
	 */
	getInterface() {
		this.http
			.get(`custominterfaces/${this.interfaceName}/`, { responseType: 'text'})
			.toPromise()
			.then(data => {
				//Remove our existing iframe if applicable
				if (this.main.nativeElement.lastChild)
					this.main.nativeElement.removeChild(this.main.nativeElement.lastChild);

				this.activeIFrame = document.createElement('iframe');
				(this.activeIFrame as any).srcdoc = data;
				this.activeIFrame.src = 'data:text/html;charset=utf-8,' + data;

				this.main.nativeElement.appendChild(this.activeIFrame);
			})
			.catch(e => this.toastrService.error(`Error retrieving interface: ${e.message}`));
	}
}
