import tests.config
import walkoff.appgateway
import walkoff.config


def initialize_test_config():
    walkoff.config.Config = tests.config.TestConfig
    walkoff.config.setup_logger()
    walkoff.appgateway.clear_cache()
    walkoff.appgateway.cache_apps(walkoff.config.Config.APPS_PATH)
    walkoff.config.app_apis = {}
    walkoff.config.load_app_apis()
