import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { plainToClass } from 'class-transformer';

import { UtilitiesService } from '../utilities.service';
import { ReportService } from '../reports/report.service';
import { User } from '../models/user';

@Injectable()
export class MainService {
	constructor (private http: HttpClient, private utils: UtilitiesService) { }

	/**
	 * Grabs username from API endpoint to fill out users info
	 * @param username
	 */
	getUser(username: string):  Promise<User>{
		return this.http.get(`api/users/personal_data/${username}`)
			.toPromise()
			.then((data) => plainToClass(User, data))
			.catch(this.utils.handleResponseError);
	}

	updateUser(data: any):  Promise<User>{
		return this.http.put(`api/users/personal_data/${data.old_username}`, data)
			.toPromise()
			.then((data) => plainToClass(User, data))
			//.catch(this.utils.handleResponseError);
	}

}
