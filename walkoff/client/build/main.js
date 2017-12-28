"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var platform_browser_dynamic_1 = require("@angular/platform-browser-dynamic");
var main_module_1 = require("./main.module");
if (sessionStorage.getItem('refresh_token')) {
    platform_browser_dynamic_1.platformBrowserDynamic().bootstrapModule(main_module_1.MainModule);
}
else {
    location.href = '/login';
}
