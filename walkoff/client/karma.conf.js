module.exports = (config) => {
	// const coverage = config.singleRun ? ['coverage'] : [];
	let plugins = [
		'karma-jasmine',
		'karma-webpack',
		'karma-coverage',
		'karma-chrome-launcher',
		'karma-remap-istanbul',
		'karma-sourcemap-loader',
		// 'karma-jasmine-html-reporter',
		// 'karma-coverage-istanbul-reporter',
	];

	let configuration = {
		basePath: '',
		frameworks: ['jasmine'],

		// plugins: [
		// 	'karma-jasmine',
		// 	'karma-webpack',
		// 	'karma-coverage',
		// 	'karma-chrome-launcher',
		// 	'karma-remap-istanbul',
		// 	// 'karma-jasmine-html-reporter',
		// 	// 'karma-coverage-istanbul-reporter',
		// ],
		plugins,

		client: {
			clearContext: false // leave Jasmine Spec Runner output visible in browser
		},

		coverageIstanbulReporter: {
			reports: ['html', 'lcovonly'],
			fixWebpackSourcePaths: true
		},

		files: [
			{ pattern: 'spec-bundle.js', watched: false },
			// '**/*.spec.ts'
			// './tests.entry.ts',
			// {
			// 	pattern: '**/*.map',
			// 	served: true,
			// 	included: false,
			// 	watched: true,
			// },
		],

		proxies: {
			'/assets/': '/base/src/assets/',
		},

		preprocessors: {
			'spec-bundle.js': ['webpack', 'sourcemap', 'coverage']
			// './src/tests.entry.ts': [
			// 	'webpack',
			// 	'sourcemap',
			// ],
			// './src/**/!(*.test|tests.*).(ts|js)': [
			// 	'sourcemap',
			// ],
		},

		webpack: require('./webpack.test')({ env: 'test' }),
		// {
		// 	plugins,
		// 	entry: './tests.entry.ts',
		// 	devtool: 'inline-source-map',
		// 	resolve: {
		// 		extensions: ['.webpack.js', '.web.js', '.ts', '.js'],
		// 	},
		// 	module: {
		// 		rules: combinedLoaders().concat(config.singleRun ? [ loaders.istanbulInstrumenter ]	: [ ]),
		// 	},
		// 	stats: { colors: true, reasons: true },
		// },
		coverageReporter: {
			type: 'in-memory'
		},

		remapCoverageReporter: {
			'text-summary': null,
			json: './coverage/coverage.json',
			html: './coverage/html'
		},

		// Webpack please don't spam the console when running in karma!
		webpackMiddleware: {
			// webpack-dev-middleware configuration
			// i.e.
			noInfo: true,
			// and use stats to turn off verbose output
			stats: {
				// options i.e. 
				chunks: false
			}
		},

		exclude: [
			'node_modules/**/*.spec.ts'
		],

		reporters: ['mocha', 'coverage', 'remap-coverage'],
		// reporters: ['spec'].concat(coverage),

		// coverageReporter: {
		// 	reporters: [
		// 		{ type: 'json' },
		// 	],
		// 	dir: './coverage/',
		// 	subdir: (browser) => {
		// 		return browser.toLowerCase().split(/[ /-]/)[0]; // returns 'chrome'
		// 	},
		// },

		reporters: ['progress'],
		port: 9876,
		browsers: ['Chrome'], // Alternatively: 'PhantomJS'
		colors: true,
		logLevel: config.LOG_INFO,
		autoWatch: true,
		captureTimeout: 6000,
		customLaunchers: {
			ChromeTravisCi: {
				base: 'Chrome',
				flags: ['--no-sandbox']
			}
		},
	};

	if (process.env.TRAVIS) {
		configuration.browsers = [
			'ChromeTravisCi'
		];

		configuration.singleRun = true;
	}

	config.set(configuration);
};