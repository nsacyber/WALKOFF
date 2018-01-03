"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var Configuration = (function () {
    function Configuration() {
    }
    Configuration.getDefaultConfiguration = function () {
        return {
            workflows_path: './data/workflows',
            db_path: './data/walkoff.db',
            walkoff_db_type: 'sqlite',
            case_db_path: './data/events.db',
            case_db_type: 'sqlite',
            clear_case_db_on_startup: false,
            log_config_path: './data/log/logging.json',
            host: '127.0.0.1',
            port: 5000,
            access_token_duration: 15,
            refresh_token_duration: 30,
            zmq_requests_address: 'tcp://127.0.0.1:5555',
            zmq_results_address: 'tcp://127.0.0.1:5556',
            zmq_communication_address: 'tcp://127.0.0.1:5557',
        };
    };
    return Configuration;
}());
exports.Configuration = Configuration;
