import { Injectable } from '@angular/core';
import { Http, Response, Headers, RequestOptions } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';


@Injectable()
export class PlaybookService {
	constructor (private authHttp: JwtHttp) {
	}
}
