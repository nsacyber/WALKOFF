from .app import app, create_app
from .blueprints import register_blueprints
from .endpoints import setup_case_stream

register_blueprints()
setup_case_stream()


