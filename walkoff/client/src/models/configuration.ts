export class Configuration {
	static getDefaultConfiguration(): Configuration {
		return {
			workflows_path: './data/workflows',
			db_path: './data/walkoff.db',
			walkoff_db_type: 'sqlite',
			case_db_path: './data/events.db',
			case_db_type: 'sqlite',
			clear_case_db_on_startup: false,
			log_config_path: './data/log/logging.json',
			// https: false,
			// tls_version: '1.2',
			// certificate_path: 'data/shortstop.public.pem',
			// private_key_path: 'data/shortstop.private.pem',
			// debug: true,
			// default_server: true,
			host: '127.0.0.1',
			port: 5000,
			access_token_duration: 15,
			refresh_token_duration: 30,
			zmq_requests_address: 'tcp://127.0.0.1:5555',
			zmq_results_address: 'tcp://127.0.0.1:5556',
			zmq_communication_address: 'tcp://127.0.0.1:5557',
			number_processes: 4,
			number_threads_per_process: 3,
		};
	}

	workflows_path: string;
	db_path: string;
	walkoff_db_type: string;
	case_db_path: string;
	case_db_type: string;
	clear_case_db_on_startup: boolean;
	log_config_path: string;
	// https: boolean;
	// tls_version: string;
	// certificate_path: string;
	// private_key_path: string;
	// debug: boolean;
	// default_server: boolean;
	host: string;
	port: number;
	access_token_duration: number; //in minutes
	refresh_token_duration: number; //in days
	zmq_requests_address: string;
	zmq_results_address: string;
	zmq_communication_address: string;
	number_processes: number;
	number_threads_per_process: number;
}
