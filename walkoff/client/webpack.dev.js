/**
 * @author: @AngularClass
 */

const helpers = require('./helpers');
const webpackMerge = require('webpack-merge'); // used to merge webpack configs
// const webpackMergeDll = webpackMerge.strategy({
// 	plugins: 'replace'
// });
const commonConfig = require('./webpack.common.js'); // the settings that are common to prod and dev

/**
 * Webpack Plugins
 */
const AddAssetHtmlPlugin = require('add-asset-html-webpack-plugin');
const DefinePlugin = require('webpack/lib/DefinePlugin');
// const NamedModulesPlugin = require('webpack/lib/NamedModulesPlugin');
// const LoaderOptionsPlugin = require('webpack/lib/LoaderOptionsPlugin');

/**
 * Webpack Constants
 */
const ENV = process.env.ENV = process.env.NODE_ENV = 'development';
const HOST = process.env.HOST || 'localhost';
const PORT = process.env.PORT || 3000;
const HMR = helpers.hasProcessFlag('hot');
const METADATA = webpackMerge(commonConfig(
	{
		env: ENV
	}).metadata,
	{
		host: HOST,
		port: PORT,
		ENV: ENV,
		HMR: HMR
	}
);

// const DllBundlesPlugin = require('webpack-dll-bundles-plugin').DllBundlesPlugin;

/**
 * Webpack configuration
 *
 * See: http://webpack.github.io/docs/configuration.html#cli
 */
module.exports = function (options) {
	return webpackMerge(commonConfig(
		{
			env: ENV
		}),
		{
			devtool: 'cheap-module-source-map',
			output: {
				path: helpers.root('dist'),
				filename: '[name].bundle.js',
				sourceMapFilename: '[file].map',
				chunkFilename: '[id].chunk.js',
				library: 'ac_[name]',
				libraryTarget: 'var',
			},

			module: {
				rules: [
					// {
					// 	test: /\.ts$/,
					// 	use: [{
					// 		loader: 'tslint-loader',
					// 		options: {
					// 			configFile: 'tslint.json'
					// 		}
					// 	}],
					// 	exclude: [/\.(spec|e2e)\.ts$/]
					// },
					{
						test: /\.css$/,
						use: ['style-loader', 'css-loader'],
						include: [helpers.root('src', 'styles')]
					},
					{
						test: /\.scss$/,
						use: ['style-loader', 'css-loader', 'sass-loader'],
						include: [helpers.root('src', 'styles')]
					},
				]
			},

			plugins: [
				new DefinePlugin({
					'ENV': JSON.stringify(METADATA.ENV),
					'HMR': METADATA.HMR,
					'process.env': {
						'ENV': JSON.stringify(METADATA.ENV),
						'NODE_ENV': JSON.stringify(METADATA.ENV),
						'HMR': METADATA.HMR,
					}
				}),

				// new DllBundlesPlugin({
				// 	bundles: {
				// 		polyfills: [
				// 			'core-js',
				// 			{
				// 				name: 'zone.js',
				// 				path: 'zone.js/dist/zone.js'
				// 			},
				// 			{
				// 				name: 'zone.js',
				// 				path: 'zone.js/dist/long-stack-trace-zone.js'
				// 			},
				// 		],
				// 		vendor: [
				// 			'@angular/platform-browser',
				// 			'@angular/platform-browser-dynamic',
				// 			'@angular/core',
				// 			'@angular/common',
				// 			'@angular/forms',
				// 			'@angular/http',
				// 			'@angular/router',
				// 			'@angularclass/hmr',
				// 			'rxjs',
				// 		]
				// 	},
				// 	dllDir: helpers.root('dll'),
				// 	webpackConfig: webpackMergeDll(commonConfig(
				// 		{
				// 			env: ENV
				// 		}),
				// 		{
				// 			devtool: 'cheap-module-source-map',
				// 			plugins: []
				// 		}
				// 	)
				// }),
				// new AddAssetHtmlPlugin([
				// 	{
				// 		filepath: helpers.root(`dll/${DllBundlesPlugin.resolveFile('polyfills')}`)
				// 	},
				// 	{
				// 		filepath: helpers.root(`dll/${DllBundlesPlugin.resolveFile('vendor')}`)
				// 	}
				// ]),

				/**
				 * Plugin: NamedModulesPlugin (experimental)
				 * Description: Uses file names as module name.
				 *
				 * See: https://github.com/webpack/webpack/commit/a04ffb928365b19feb75087c63f13cadfc08e1eb
				 */
				// new NamedModulesPlugin(),

				/**
				 * Plugin LoaderOptionsPlugin (experimental)
				 *
				 * See: https://gist.github.com/sokra/27b24881210b56bbaff7
				 */
				// new LoaderOptionsPlugin({
				// 	debug: true,
				// 	options: {

				// 	}
				// }),
			],

			/**
			 * Webpack Development Server configuration
			 * Description: The webpack-dev-server is a little node.js Express server.
			 * The server emits information about the compilation state to the client,
			 * which reacts to those events.
			 *
			 * See: https://webpack.github.io/docs/webpack-dev-server.html
			 */
			// devServer: {
			// 	port: METADATA.port,
			// 	host: METADATA.host,
			// 	historyApiFallback: true,
			// 	watchOptions: {
			// 		aggregateTimeout: 300,
			// 		poll: 1000
			// 	},
			// 	proxy: {
			// 		'/api': {
			// 			target: 'http://localhost:8080',
			// 			secure: false
			// 		},
			// 		'/oauth': {
			// 			target: 'http://localhost:8080',
			// 			secure: false
			// 		}
			// 	}
			// },

			/*
			 * Include polyfills or mocks for various node stuff
			 * Description: Node configuration
			 *
			 * See: https://webpack.github.io/docs/configuration.html#node
			 */
			node: {
				global: true,
				crypto: 'empty',
				process: true,
				module: false,
				clearImmediate: false,
				setImmediate: false
			}
		}
	);
}