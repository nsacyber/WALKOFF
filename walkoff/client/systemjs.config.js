(function (global) {
	var paths = {
		'npm:': 'client/node_modules/'
	};
	// map tells the System loader where to look for things
	var map = {
		// 'login': 'client/modules/login',
		'main': 'client/build',
		'models': 'client/models',
		'rxjs': 'npm:rxjs',
		'@angular': 'npm:@angular',
		'angular2-datatable': 'npm:angular2-datatable',
		'lodash': 'npm:lodash',
		'jquery': 'npm:jquery/dist/jquery.min.js',
		'ts': 'npm:plugin-typescript/lib/plugin.js',
		'tsconfig.json': 'client/tsconfig.json',
		'typescript': 'npm:typescript/lib/typescript.js',
		'@ng-bootstrap/ng-bootstrap': 'npm:@ng-bootstrap/ng-bootstrap/bundles/ng-bootstrap.js',
		'@swimlane/ngx-datatable': 'npm:@swimlane/ngx-datatable/release/index.js',
		'ng2-toasty': 'npm:ng2-toasty/bundles/index.umd.js',
		'ng2-select2': 'npm:ng2-select2/ng2-select2.bundle.js',
		'ngx-contextmenu': 'npm:ngx-contextmenu/lib/ngx-contextmenu.js',
		'd3': 'npm:d3/build/d3.node.js',
		'angular2-jwt': 'npm:angular2-jwt/angular2-jwt.js',
		'angular2-jwt-refresh': 'npm:angular2-jwt-refresh/dist/angular2-jwt-refresh.js',
		'ng-pick-datetime': 'npm:ng-pick-datetime',
		'moment': 'npm:moment',
		'cytoscape': 'npm:cytoscape/dist',
		'cytoscape-clipboard': 'npm:cytoscape-clipboard/cytoscape-clipboard.js',
		'cytoscape-edgehandles': 'npm:cytoscape-edgehandles/cytoscape-edgehandles.js',
		'cytoscape-grid-guide': 'npm:cytoscape-grid-guide/cytoscape-grid-guide.js',
		'cytoscape-panzoom': 'npm:cytoscape-panzoom/cytoscape-panzoom.js',
		'cytoscape-undo-redo': 'npm:cytoscape-undo-redo/cytoscape-undo-redo.js',
		'jstree': 'npm:jstree/dist',
		'angular2-uuid': 'npm:angular2-uuid/index.js',
		'ng2-dnd': 'npm:ng2-dnd/bundles/index.umd.js'
	};

	// packages tells the System loader how to load when no filename and/or no extension
	var packages = {
		// 'login': { main: 'login',  defaultExtension: 'ts' },
		'main': { main: 'main', defaultExtension: 'js' },
		'models': { defaultExtension: 'ts' },
		'rxjs': { main: 'Rx', defaultExtension: 'js' },
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
		'cytoscape': { main: 'cytoscape.js', defaultExtension: 'js' },
		'jstree': { main: 'jstree.min.js', defaultExtension: 'js' },
		// 'uuid': { main: 'index.js', defaultExtension: 'js' },
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
		map[pkgName] = `npm:${pkgName}/build/${pkgName}.min.js`;
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