import { Component } from '@angular/core';

import { LoginService } from './login.service';

@Component({
	selector: 'login-component',
	templateUrl: 'client/login/login.html',
	//styleUrls: ['./style.css'],
	providers: [LoginService]
})
export class LoginComponent {
	username:string;
	password:string;

	constructor(private loginService: LoginService) {
	}

//	login(): void {
//		this.loginService.login(this.username, this.password)
//		.then(function (success) {
//			//route to main module
//			console.log('successfully authenticated user: ' + this.username);
//		})
//		.catch(function (error) {
//			console.log(error.message);
//		});
//	};
}