from os import sep
from os.path import join

test_path = join('.', 'tests')
test_workflows_path = join('.', 'tests', 'testWorkflows') + sep
test_workflows_path_with_generated = join('.', 'tests', 'testWorkflows', 'testGeneratedWorkflows') + sep
test_workflows_backup_path = join('.', 'tests', 'testWorkflows', 'testGeneratedWorkflows_bkup') + sep
test_apps_path = join('.', 'tests', 'apps')
test_data_dir_name = 'testdata'
test_data_path = join('.', 'tests', test_data_dir_name)
test_appdevice_backup = join(test_data_path, 'appdevice.json')
test_cases_backup = join(test_data_path, 'cases.json')

test_logging_config = \
    {
        "version": 1,
        "disable_existing_loggers": True,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "CRITICAL",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "server": {
                "level": "CRITICAL",
                "handlers": ["console"],
                "propagate": 0
            },
            "core": {
                "level": "CRITICAL",
                "handlers": ["console"]
            }
        },
        "root": {
            "level": "CRITICAL",
            "handlers": ["console"]
        }
    }
