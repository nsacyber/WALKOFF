(function(global) {

	// map tells the System loader where to look for things
	var map = {
		// 'login': 'client/modules/login',
		'main': 'client/build',
		// 'npm:' : 'client/node_modules/',
		'models': 'client/models',
		'rxjs': 'client/node_modules/rxjs',
		//'angular2-in-memory-web-api': 'client/node_modules/angular2-in-memory-web-api',
		'@angular': 'client/node_modules/@angular',
		'angular2-datatable': 'client/node_modules/angular2-datatable',
		'lodash': 'client/node_modules/lodash',
		'jquery': 'client/node_modules/jquery/dist/jquery.min.js',
		'ts': 'client/node_modules/plugin-typescript/lib/plugin.js',
		'tsconfig.json': 'client/tsconfig.json',
		'typescript': 'client/node_modules/typescript/lib/typescript.js',
		'@ng-bootstrap/ng-bootstrap': 'client/node_modules/@ng-bootstrap/ng-bootstrap/bundles/ng-bootstrap.js',
		'@swimlane/ngx-datatable': 'client/node_modules/@swimlane/ngx-datatable/release/index.js',
		'ng2-toasty': 'client/node_modules/ng2-toasty/bundles/index.umd.js',
		'ng2-select2': 'client/node_modules/ng2-select2/ng2-select2.bundle.js',
		'ngx-contextmenu': 'client/node_modules/ngx-contextmenu/lib/ngx-contextmenu.js',
	};

	// packages tells the System loader how to load when no filename and/or no extension
	var packages = {
		// 'login': { main: 'login',  defaultExtension: 'ts' },
		'main': { main: 'main',  defaultExtension: 'js' },
		'models': { defaultExtension: 'ts' },
		'rxjs': { defaultExtension: 'js' },
		'ts': { defaultExtension: 'js' },
		'lodash': { main: 'index.js', defaultExtension: 'js' },
		'angular2-datatable': { main: 'index.js', defaultExtension: 'js' },
		//'angular2-in-memory-web-api': { defaultExtension: 'js' },
	};

	var ngPackageNames = [
		'common',
		'compiler',
		'core',
		'forms',
		'http',
		'platform-browser',
		'platform-browser-dynamic',
		'router',
		'router-deprecated',
		'testing',
		'upgrade',
	];

	// add package entries for angular packages in the form '@angular/common': { main: 'index.js', defaultExtension: 'js' }
	ngPackageNames.forEach(function(pkgName) {
		packages["@angular/" + pkgName] = {
			main: 'bundles/' + pkgName + '.umd.min.js', 
			//defaultExtension: 'js'
		};
	});

	var config = {
		map: map,
		packages: packages,
		// transpiler: 'ts',
		// typescriptOptions: { 
		// 	tsconfig: true
		// },
		// meta: {
		// 	typescript: {
		// 		exports: "ts"
		// 	}
		// }
	};

	// filterSystemConfig - index.html's chance to modify config before we register it.
	if (global.filterSystemConfig) { global.filterSystemConfig(config); }

	SystemJS.config(config);
})(this);