export class Configuration {
	workflows_path: string;
	templates_path: string;
	// profile_visualizations_path: string;
	// keywords_path: string;
	db_path: string;
	walkoff_db_type: string;
	case_db_path: string;
	case_db_type: string;
	clear_case_db_on_startup: boolean;
	log_config_path: string;
	https: boolean;
	tls_version: string;
	// certificate_path: string;
	// private_key_path: string;
	// debug: boolean;
	// default_server: boolean;
	host: string;
	port: number;
	access_token_duration: number; //in minutes
	refresh_token_duration: number; //in days

	static getDefaultConfiguration(): Configuration {
		return {
			workflows_path: './data/workflows',
			templates_path: './data/templates',
			// profile_visualizations_path: 'tests/profileVisualizations',
			// keywords_path: 'core/keywords',
			db_path: './data/walkoff.db',
			walkoff_db_type: 'sqlite',
			case_db_path: './data/events.db',
			case_db_type: 'sqlite',
			clear_case_db_on_startup: false,
			log_config_path: './data/log/logging.json',
			https: false,
			tls_version: '1.2',
			// certificate_path: 'data/shortstop.public.pem',
			// private_key_path: 'data/shortstop.private.pem',
			// debug: true,
			// default_server: true,
			host: '127.0.0.1',
			port: 5000,
			access_token_duration: 15,
			refresh_token_duration: 30,
		};
	}
}