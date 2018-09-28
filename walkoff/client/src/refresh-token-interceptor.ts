import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { AuthService } from './auth/auth.service';
import { JwtInterceptor } from '@auth0/angular-jwt';


@Injectable()
export class RefreshTokenInterceptor implements HttpInterceptor {

    constructor (private authService: AuthService, private jwtInterceptor: JwtInterceptor) {}

    intercept (req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        if (this.jwtInterceptor.isWhitelistedDomain(req) && !this.jwtInterceptor.isBlacklistedRoute(req) && this.authService.isAccessTokenExpired()) {
            return Observable
                .fromPromise(this.authService.getAccessTokenRefreshed())
                .mergeMap(() => this.jwtInterceptor.intercept(req, next));
        } 
        else {
            return next.handle(req);
        }
    }

}