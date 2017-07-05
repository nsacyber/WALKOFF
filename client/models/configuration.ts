export class Configuration {
	workflows_path: string = 'data/workflows';
	templates_path: string = 'data/templates';
	profile_visualizations_path: string = 'tests/profileVisualizations';
	keywords_path: string = 'core/keywords';
	db_path: string = 'data/walkoff.db';
	https: boolean = false;
	tls_version: string = '1.2';
	certificate_path: string = 'data/shortstop.public.pem';
	private_key_path: string = 'data/shortstop.private.pem';
	debug: boolean = true;
	default_server: boolean = true;
	host: string = '127.0.0.1';
	port: number = 5000;
}