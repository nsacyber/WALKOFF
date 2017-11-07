import { Component } from '@angular/core';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';

import { DashboardService } from './dashboard.service';

@Component({
	selector: 'dashboard-component',
	templateUrl: 'client/dashboard/dashboard.html',
	styleUrls: [
		'client/dashboard/dashboard.css',
	],
	providers: [DashboardService],
})
export class DashboardComponent {
	currentDashboard: string;

	constructor(
		private dashboardService: DashboardService, private toastyService: ToastyService, 
		private toastyConfig: ToastyConfig) {
		this.currentDashboard = 'Default Dashboard';
	}

	ngAfterViewInit() {
		const addLink = (script: string) => {
			const s = document.createElement('link');
			s.rel = 'stylesheet';
			s.href = script;
			document.body.appendChild(s);
		};

		const addScript = (script: string) => {
			const s = document.createElement('script');
			s.type = 'text/javascript';
			s.src = script;
			s.async = false;
			document.body.appendChild(s);
		};
	}
}
