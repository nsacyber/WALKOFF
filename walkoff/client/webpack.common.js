/**
 * @author: @AngularClass
 */

const webpack = require('webpack');
const helpers = require('./helpers');

// /**
//  * Webpack Plugins
//  */
const AssetsPlugin = require('assets-webpack-plugin');
// const NormalModuleReplacementPlugin = require('webpack/lib/NormalModuleReplacementPlugin');
// const ContextReplacementPlugin = require('webpack/lib/ContextReplacementPlugin');
// const CopyWebpackPlugin = require('copy-webpack-plugin');
const CheckerPlugin = require('awesome-typescript-loader').CheckerPlugin;
// const HtmlElementsPlugin = require('./html-elements-plugin');
// const HtmlWebpackPlugin = require('html-webpack-plugin');
// const LoaderOptionsPlugin = require('webpack/lib/LoaderOptionsPlugin');
// const ScriptExtHtmlWebpackPlugin = require('script-ext-html-webpack-plugin');
// const ngcWebpack = require('ngc-webpack');
const ProvidePlugin = require('webpack/lib/ProvidePlugin')

/**
 * Webpack Constants
 */
const HMR = helpers.hasProcessFlag('hot');
const AOT = helpers.hasNpmFlag('aot');
const METADATA = {
	title: 'Modified Angular2 Webpack Starter by @gdi2290 from @AngularClass',
	baseUrl: '/',
	isDevServer: helpers.isWebpackDevServer()
};

/**
 * Webpack configuration
 *
 * See: http://webpack.github.io/docs/configuration.html#cli
 */
module.exports = function (options) {
	isProd = options.env === 'production';
	return {
		resolve: {
			extensions: ['.ts', '.js', '.json'],
			modules: [helpers.root('src'), helpers.root('node_modules')]
		},
		// devtool: 'cheap-module-source-map',
		entry: {
			'polyfills': './src/polyfills.ts',
			'main': AOT ? './src/main.aot.ts' : './src/main.ts',
		},
		output: {
			path: helpers.root('dist'),
			filename: '[name].bundle.js',
			sourceMapFilename: '[file].map',
			chunkFilename: '[name].bundle.js',
			library: 'ac_[name]',
			libraryTarget: 'var',
		},

		module: {
			rules: [
				{
					test: /\.ts$/,
					use: [
						{
							loader: '@angularclass/hmr-loader',
							options: {
								pretty: !isProd,
								prod: isProd
							}
						},
						{
							loader: 'awesome-typescript-loader',
							options: {
								configFileName: 'tsconfig.webpack.json'
							}
						},
						{
							loader: 'angular2-template-loader'
						}
					],
					exclude: [/\.(spec|e2e)\.ts$/]
				},
				{
					test: /\.css$/,
					use: ['to-string-loader', 'style-loader', 'css-loader'],
					exclude: [helpers.root('styles')]
				},
				{
					test: /\.scss$/,
					use: ['to-string-loader', 'css-loader', 'sass-loader'],
					exclude: [helpers.root('styles')]
				},
				{
					test: /\.html$/,
					use: 'raw-loader',
					exclude: [helpers.root('index.html')]
				},
				{
					test: /\.(jpg|png|gif)$/,
					use: 'file-loader'
				},
				{
					test: /.(ttf|otf|eot|svg|woff(2)?)(\?[a-z0-9]+)?$/,
					use: [{
						loader: 'file-loader',
						options: {
							name: '[name].[ext]',
							// outputPath: 'dist/',    // where the fonts will go
							publicPath: '/client/dist/'       // override the default path
						}
					}]
				}
			]
		},
		optimization: {
			splitChunks: {
				cacheGroups: {
					vendors: {
						test: /[\\/]node_modules[\\/]/,
						name: 'vendor',
						enforce: true,
						chunks: chunk => chunk.name == 'main'
					}
				}
			},
		},
		plugins: [
			// new AssetsPlugin({
			// 	path: helpers.root('dist'),
			// 	filename: 'webpack-assets.json',
			// 	prettyPrint: true
			// }),

			new CheckerPlugin(),

			new ProvidePlugin({
				$: "jquery",
				jQuery: "jquery",
			}),

			// new ContextReplacementPlugin(
			// 	// The (\\|\/) piece accounts for path separators in *nix and Windows
			// 	/angular(\\|\/)core(\\|\/)@angular/,
			// 	helpers.root('src'), // location of your src
			// 	{
			// 		// your Angular Async Route paths relative to this root directory
			// 	}
			// ),

			// new CopyWebpackPlugin([
			// 	{ from: 'src/assets', to: 'assets' },
			// 	{ from: 'src/meta'}
			// ]),

			// new HtmlWebpackPlugin({
			// 	template: 'src/index.html',
			// 	title: METADATA.title,
			// 	chunksSortMode: 'dependency',
			// 	metadata: METADATA,
			// 	inject: 'head'
			// }),

			// new ScriptExtHtmlWebpackPlugin({
			// 	defaultAttribute: 'defer'
			// }),

			// new HtmlElementsPlugin({
			// 	headTags: require('./head-config.common')
			// }),

			// new LoaderOptionsPlugin({}),
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
	};
}