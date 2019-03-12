from __future__ import with_statement

import os
import sys

sys.path.append(os.getcwd())

# Need all these imports
from api_gateway.serverdb.mixins import *
from api_gateway.serverdb.resource import *
from api_gateway.serverdb.scheduledtasks import *
from api_gateway.serverdb.tokens import *
from api_gateway.serverdb.user import *
from api_gateway.migrations.database.commonenv import run
from api_gateway.extensions import db
from api_gateway.server.app import app
import api_gateway.config

# unclear if commented out app creation is necessary, but may need it in the future
# api_gateway.config.initialize()
# app = create_app()
# app_context = app.test_request_context()
# app_context.push()

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


run(target_metadata)
