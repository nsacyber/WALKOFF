import { Component } from '@angular/core';

@Component({
	selector: 'main-component',
	templateUrl: 'client/main/main.html',
	styleUrls: [
		'client/main/main.css',
		// 'client/components/main/AdminLTE.css',
		// 'client/components/main/skin-blue.min.css',
		// 'client/node_modules/bootstrap/dist/css/bootstrap.min.css',
		// 'client/node_modules/font-awesome/css/font-awesome.min.css',
	],
})
export class MainComponent {
	currentUser: string;

	constructor() { 
		this.currentUser = localStorage.getItem('currentUser');
	}
}