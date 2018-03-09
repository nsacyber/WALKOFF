// import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { MainModule } from './main.module';

// Import global JS packages
import 'jquery';
import 'bootstrap';
import 'select2';

// Import global CSS packages
import 'bootstrap/dist/css/bootstrap.min.css';
import '@swimlane/ngx-datatable/release/index.css';
import '@swimlane/ngx-datatable/release/themes/material.css';
import '@swimlane/ngx-datatable/release/assets/icons.css';
import 'font-awesome/css/font-awesome.min.css';
import 'ng2-toasty/style-bootstrap.css';
import 'select2/dist/css/select2.min.css';

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
