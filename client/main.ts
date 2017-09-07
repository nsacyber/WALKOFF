import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { MainModule } from './main.module';

if (sessionStorage.getItem('refresh_token')) {
	platformBrowserDynamic().bootstrapModule(MainModule);

	// Enable production mode unless running locally
	if (!/localhost/.test(document.location.host)) {
		enableProdMode();
	}
}
else
	location.href = '/login';