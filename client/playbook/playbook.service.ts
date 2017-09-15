import { Injectable } from '@angular/core';
import { Http, Response, Headers } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';


@Injectable()
export class PlaybookService {
	constructor (private authHttp: JwtHttp) {
	}
}
