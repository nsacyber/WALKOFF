// import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { MainModule } from './main.module';

import 'jquery';
import 'bootstrap';
import 'select2';

document.addEventListener('DOMContentLoaded', event => {
	if (sessionStorage.getItem('refresh_token')) {
		//TODO: figure out a good way of handling this
		// Enable production mode unless running locally
		// if (!/localhost/.test(document.location.host)) {
		// 	enableProdMode();
		// }

		platformBrowserDynamic().bootstrapModule(MainModule);
	} else { location.href = '/login'; }
});
