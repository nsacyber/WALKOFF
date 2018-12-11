from __future__ import with_statement

import os
import sys

sys.path.append(os.getcwd())

# Need all these imports
from walkoff.executiondb.action import Action
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.branch import Branch
from walkoff.executiondb.condition import Condition
from walkoff.executiondb.conditionalexpression import ConditionalExpression
from walkoff.executiondb.device import *
from walkoff.executiondb.executionelement import *
from walkoff.executiondb.metrics import *
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.position import Position
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb.transform import Transform
from walkoff.executiondb.workflow import Workflow
from walkoff.executiondb.workflowresults import *
from walkoff.executiondb import Execution_Base
from walkoff.migrations.database.commonenv import run

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Execution_Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

run(target_metadata)
