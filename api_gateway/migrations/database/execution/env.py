from __future__ import with_statement

import os
import sys

sys.path.append(os.getcwd())

# Need all these imports
from api_gateway.executiondb.action import Action
from api_gateway.executiondb.argument import Argument
from api_gateway.executiondb.branch import Branch
# from api_gateway.executiondb.condition import Condition
# from api_gateway.executiondb.conditionalexpression import ConditionalExpression
from api_gateway.executiondb.executionelement import *
from api_gateway.executiondb.metrics import *
from api_gateway.executiondb.playbook import Playbook
from api_gateway.executiondb.position import Position
# from api_gateway.executiondb.transform import Transform
from api_gateway.executiondb.workflow import Workflow
from api_gateway.executiondb.workflowresults import *
from api_gateway.executiondb import Execution_Base
from api_gateway.migrations.database.commonenv import run

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
