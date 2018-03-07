from __future__ import with_statement

import os
import sys

sys.path.append(os.getcwd())

# Need all these imports
from walkoff.executiondb.action import *
from walkoff.executiondb.argument import *
from walkoff.executiondb.branch import *
from walkoff.executiondb.condition import *
from walkoff.executiondb.conditionalexpression import *
from walkoff.executiondb.device import *
from walkoff.executiondb.executionelement import *
from walkoff.executiondb.playbook import *
from walkoff.executiondb.position import *
from walkoff.executiondb.saved_workflow import *
from walkoff.executiondb.transform import *
from walkoff.executiondb.workflow import *
from walkoff.executiondb.workflowresults import *
from scripts.migrations.database.commonenv import run
from walkoff.executiondb.device import Device_Base

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Device_Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

run(target_metadata)
