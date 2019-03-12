from __future__ import with_statement

import os
import sys

sys.path.append(os.getcwd())

from api_gateway.migrations.database.commonenv import run

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

run(target_metadata)
