import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, from } from 'rxjs';
import { mergeMap } from 'rxjs/operators';
import { AuthService } from './auth/auth.service';
import { JwtInterceptor } from '@auth0/angular-jwt';


export function jwtOptionsFactory(authService: AuthService)  {
    return {
        tokenGetter: () => authService.getAccessToken(),
		blacklistedRoutes: ['login', 'api/auth', 'api/auth/logout', 'api/auth/refresh']
    }
}

export function jwtTokenGetter() : string {
    return sessionStorage.getItem('access_token');
}

@Injectable()
export class RefreshTokenInterceptor implements HttpInterceptor {

    constructor (private authService: AuthService, private jwtInterceptor: JwtInterceptor) {}

    intercept (req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        if (this.jwtInterceptor.isWhitelistedDomain(req) && !this.jwtInterceptor.isBlacklistedRoute(req) && this.authService.isAccessTokenExpired()) {
            return from(this.authService.getAccessTokenRefreshed())
                    .pipe(mergeMap(() => this.jwtInterceptor.intercept(req, next)));
        } 
        else {
            return next.handle(req);
        }
    }
}