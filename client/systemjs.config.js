(function (global) {
	var paths = {
		'npm:': 'client/node_modules/'
	};
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
		'd3': 'client/node_modules/d3/build/d3.node.js',
		'ng-pick-datetime': 'npm:ng-pick-datetime',
		'moment': 'npm:moment',
	};

	// packages tells the System loader how to load when no filename and/or no extension
	var packages = {
		// 'login': { main: 'login',  defaultExtension: 'ts' },
		'main': { main: 'main', defaultExtension: 'js' },
		'models': { defaultExtension: 'ts' },
		'rxjs': { defaultExtension: 'js' },
		'ts': { defaultExtension: 'js' },
		'lodash': { main: 'index.js', defaultExtension: 'js' },
		'angular2-datatable': { main: 'index.js', defaultExtension: 'js' },
		//'angular2-in-memory-web-api': { defaultExtension: 'js' },
		'ng-pick-datetime': {
			main: 'picker.bundle.js',
			defaultExtension: 'js'
		},
		'moment': {
			main: 'moment.js',
			defaultExtension: 'js'
		},
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
	ngPackageNames.forEach(function (pkgName) {
		packages["@angular/" + pkgName] = {
			main: 'bundles/' + pkgName + '.umd.min.js',
			//defaultExtension: 'js'
		};
	});

	var d3PackageNames = [
		'd3',
		'd3-array',
		'd3-axis',
		'd3-brush',
		'd3-chord',
		'd3-collection',
		'd3-color',
		'd3-dispatch',
		'd3-drag',
		'd3-dsv',
		'd3-ease',
		'd3-force',
		'd3-format',
		'd3-interpolate',
		'd3-hierarchy',
		'd3-geo',
		'd3-path',
		'd3-polygon',
		'd3-quadtree',
		'd3-queue',
		'd3-random',
		'd3-request',
		'd3-scale',
		'd3-selection',
		'd3-shape',
		'd3-time',
		'd3-time-format',
		'd3-timer',
		'd3-transition',
		'd3-voronoi',
		'd3-zoom',
	];

	d3PackageNames.forEach(function (pkgName) {
		map[pkgName] = `client/node_modules/${pkgName}/build/${pkgName}.min.js`;
	});

	var config = {
		paths: paths,
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