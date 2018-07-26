import json
import os

import semver

from walkoff.appgateway import cache_apps
from walkoff.config import load_app_apis
import walkoff.config
import importlib
from .workflows import versions as versions
from walkoff import executiondb
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.schemas import PlaybookSchema


PREV_VERSION = "0.5.0"
LATEST_VERSION = "0.7.0"


def validate_path(mode, cur, tgt):
    if cur == tgt:
        print("Target version is same as current version: {}. Cannot {}.".format(cur, mode))
        return False

    temp = cur
    while temp != tgt and temp is not None:
        temp = get_next_version(mode, temp)

    if temp == tgt:
        return True
    elif temp is None:
        print("No valid {} path from {} to {} found.".format(mode, cur, tgt))
        return False


def continue_condition(mode, cur, tgt):
    if mode == DOWNGRADE:
        return semver.compare(cur, tgt) > 0
    elif mode == UPGRADE:
        return semver.compare(cur, tgt) < 0
    else:
        return False


def get_next_version(cur):
    try:
        if mode == DOWNGRADE:
            return versions.prev_vers[cur]
        elif mode == UPGRADE:
            return versions.next_vers[cur]
    except KeyError:
        print("There is no supported {} for {}.".format(mode, cur))
        return None


def convert_playbooks(current_version, target_version, workflows_path, apps_path):
    #initialize_databases()
    cache_apps(apps_path)
    load_app_apis()


    for subd, d, files in os.walk(workflows_path):
        for f in files:
            if f.endswith('.playbook'):
                path = os.path.join(subd, f)
                convert_playbook(path, version)


def convert_playbook(path, current_version):
    print('Converting {}'.format(path))
    with open(path, 'r+') as f:
        playbook = json.load(f)

        if validate_path(mode, cur_version, tgt_version):
            next_version = ""
            while continue_condition(mode, cur_version, tgt_version) and next_version is not None:

                next_version = get_next_version(mode, cur_version)

                print("{}ing playbook from {} to {}".format(mode[:-1], cur_version, next_version))

                path = "scripts.migrations.workflows."
                rev = importlib.import_module(path + next_version.replace(".", "_"))
                if rev.upgrade_supported:
                    rev.upgrade_playbook(playbook)
                cur_version = next_version

            playbook_obj = executiondb.execution_db.session.query(Playbook).filter_by(name=playbook['name']).first()

            f.seek(0)
            json.dump(PlaybookSchema().dump(playbook_obj).data, f, sort_keys=True, indent=4, separators=(',', ': '))
            f.truncate()
