import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { MainModule } from './app/main.module';
import { environment } from './environments/environment';

document.addEventListener('DOMContentLoaded', event => {
    if (sessionStorage.getItem('refresh_token')) {

        if (environment.production) {
            enableProdMode();
        }

        platformBrowserDynamic().bootstrapModule(MainModule)
            .catch(err => console.log(err));
    }
    else { location.href = 'login'; }
});
