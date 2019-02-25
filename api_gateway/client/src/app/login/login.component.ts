import { Component, OnInit } from '@angular/core';

import { LoginService } from './login.service';

@Component({
	selector: 'login-component',
	templateUrl: './login.html',
	//styleUrls: ['./style.css'],
	providers: [LoginService],
})
/**
 * These classes/files is not actually used currently and can probably be deleted if desired.
 */
export class LoginComponent implements OnInit {
	title: string;
	username: string;
	password: string;

	constructor(private loginService: LoginService) {}

	ngOnInit(): void {
		this.title = 'New Login';
	}

	login(): void {
		this.loginService.login(this.username, this.password)
		.then(success => {
			//route to main module
			// console.log('successfully authenticated user: ' + this.username);
		})
		.catch(error => {
			// console.log(error.message);
		});
	}
}
