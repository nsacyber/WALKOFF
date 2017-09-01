import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { MainModule } from './main.module';

if (localStorage.getItem('refresh_token'))
	platformBrowserDynamic().bootstrapModule(MainModule);
else
	location.href = '/login';