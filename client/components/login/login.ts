import { Component } from '@angular/core';

import { LoginService } from '../../services/login';

@Component({
	selector: 'login-component',
	templateUrl: './login.html',
	//styleUrls: ['./style.css'],
	providers: [LoginService]
})
export class LoginComponent {
	title:string;
	username:string;
	password:string;

	constructor(private loginService: LoginService) {
		this.title = "New Login";
	}

	login(): void {
		this.loginService.login(this.username, this.password)
		.then(function (success) {
			//route to main module
			console.log('successfully authenticated user: ' + this.username);
		})
		.catch(function (error) {
			console.log(error.message);
		});
	};
}