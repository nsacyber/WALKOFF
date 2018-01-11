const helpers = require('./helpers');

module.exports = () => {
	return {
		devtool: 'inline-source-map',
		// entry: {
		// 	main: './main.ts'
		// },
		// output: {
		// 	path: './dist',
		// 	filename: '[name].bundle.js'
		// },
		resolve: {
			extensions: ['.js', '.ts'],
			modules: [helpers.root('src'), 'node_modules']
		},
		module: {
			rules: [
				{
					enforce: 'pre',
					test: /\.js$/,
					loader: 'source-map-loader',
					exclude: [
						// these packages have problems with their sourcemaps
						helpers.root('node_modules/rxjs'),
						helpers.root('node_modules/@angular')
					]
				},
				{
					test: /\.ts$/,
					use: [
						{
							loader: 'awesome-typescript-loader',
							query: {
								// use inline sourcemaps for "karma-remap-coverage" reporter
								sourceMap: false,
								inlineSourceMap: true,
								compilerOptions: {
									// Remove TypeScript helpers to be injected
									// below by DefinePlugin
									removeComments: true
								}
							},
						},
						'angular2-template-loader'
					],
					exclude: [/\.e2e\.ts$/]
				},
				// {
				// 	test: /\.json$/,
				// 	loader: 'json-loader',
				// 	exclude: [helpers.root('src/index.html')]
				// },
				{
					test: /\.css$/,
					loader: ['to-string-loader', 'css-loader'],
					// exclude: [helpers.root('index.html')]
				},
				{
					test: /\.scss$/,
					loader: ['raw-loader', 'sass-loader'],
					// exclude: [helpers.root('src/index.html')]
				},
				{
					test: /\.html$/,
					loader: 'raw-loader',
					// exclude: [helpers.root('src/index.html')]
				},
				{
					enforce: 'post',
					test: /\.(js|ts)$/,
					loader: 'istanbul-instrumenter-loader',
					include: helpers.root('src'),
					exclude: [
						/\.(e2e|spec)\.ts$/,
						/node_modules/
					]
				}
			]
		},
		performance: {
			hints: false
		},
		node: {
			global: true,
			process: false,
			crypto: 'empty',
			module: false,
			clearImmediate: false,
			setImmediate: false
		}
	};
};