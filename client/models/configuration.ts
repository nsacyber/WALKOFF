export class Configuration {
	workflows_path: string;
	templates_path: string;
	profile_visualizations_path: string;
	keywords_path: string;
	db_path: string;
	https: boolean;
	tls_version: string;
	certificate_path: string;
	private_key_path: string;
	debug: boolean;
	default_server: boolean;
	host: string;
	port: number;

	static getDefaultConfiguration(): Configuration {
		return {
			workflows_path: 'data/workflows',
			templates_path: 'data/templates',
			profile_visualizations_path: 'tests/profileVisualizations',
			keywords_path: 'core/keywords',
			db_path: 'data/walkoff.db',
			https: false,
			tls_version: '1.2',
			certificate_path: 'data/shortstop.public.pem',
			private_key_path: 'data/shortstop.private.pem',
			debug: true,
			default_server: true,
			host: '127.0.0.1',
			port: 5000
		};
	}
}