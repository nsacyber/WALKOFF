import { Component } from '@angular/core';
import { JwtHelper } from 'angular2-jwt';

import { AuthService } from '../auth/auth.service';

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
	jwtHelper: JwtHelper = new JwtHelper();

	constructor(private authService: AuthService) {
		this.updateUserInfo();
	}

	updateUserInfo(): void {
		let refreshToken = localStorage.getItem('refresh_token');
		
		let decoded = this.jwtHelper.decodeToken(refreshToken);

		this.currentUser = decoded.identity;
	}

	logout(): void {
		this.authService.logout()
			.then(() => location.href = '/login');
	}

	getKey(): void {
		window.open('/api/auth/token', 'targetWindow', 'width=925, height=150');
	}
}