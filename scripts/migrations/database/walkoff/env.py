from __future__ import with_statement

import os
import sys

sys.path.append(os.getcwd())

# Need all these imports
from walkoff.serverdb.casesubscription import *
from walkoff.serverdb.message import *
from walkoff.serverdb.mixins import *
from walkoff.serverdb.resource import *
from walkoff.serverdb.scheduledtasks import *
from walkoff.serverdb.tokens import *
from walkoff.serverdb.user import *
from scripts.migrations.database.commonenv import run
from walkoff.extensions import db
from flask import current_app


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
app_context = current_app.test_request_context()
app_context.push()

run(target_metadata)
