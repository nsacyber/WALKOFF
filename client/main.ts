import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { MainModule } from './main.module';

platformBrowserDynamic().bootstrapModule(MainModule);

// Enable production mode unless running locally
if (!/localhost/.test(document.location.host)) {
	enableProdMode();
}