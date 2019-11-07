import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { MainModule } from './app/main.module';
import { environment } from './environments/environment';

document.addEventListener('DOMContentLoaded', event => {
    if (checkLoggedIn()) {
        if (environment.production) {
            enableProdMode();
        }

        platformBrowserDynamic().bootstrapModule(MainModule)
            .catch(err => console.log(err));
    }
    else { location.href = 'login'; }

    function checkLoggedIn() : boolean  {
        return (environment.cookies) ? !!getCookie('refresh_token') : !!sessionStorage.getItem('refresh_token');
    }

    function getCookie(cname: string) {
        var name = cname + "=";
        var ca = document.cookie.split(';');
        for(var i = 0; i < ca.length; i++) {
          var c = ca[i];
          while (c.charAt(0) == ' ') {
            c = c.substring(1);
          }
          if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
          }
        }
        return "";
    };
});