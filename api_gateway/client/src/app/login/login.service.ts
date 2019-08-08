import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { UtilitiesService } from '../utilities.service';

@Injectable()
export class LoginService {
	constructor (private http: HttpClient, private utils: UtilitiesService) { }

	login(username: string, password: string): Promise<string> {
		return this.http.post('login', { username, password })
			.toPromise()
			.catch(this.utils.handleResponseError);
	}
}
