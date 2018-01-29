import json
import os
from os.path import join
import semver

import sys

sys.path.append(os.path.abspath('.'))
from walkoff.appgateway import cache_apps, clear_cache
from walkoff.config.config import load_app_apis
from tests import config as test_config
import importlib
import scripts.migrations.workflows.versions as versions
import walkoff.config.paths
import tests.config
from walkoff import initialize_databases

UPGRADE = "upgrade"
DOWNGRADE = "downgrade"


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


def get_next_version(mode, cur):
    try:
        if mode == DOWNGRADE:
            return versions.prev_vers[cur]
        elif mode == UPGRADE:
            return versions.next_vers[cur]
    except KeyError:
        print("There is no supported {} for {}.".format(mode, cur))
        return "0.7.0"


def convert_playbooks(mode, tgt_version):
    initialize_databases()
    cache_apps(join('.', 'apps'))
    load_app_apis()
    for subd, d, files in os.walk(join('workflows')):
        for f in files:
            if f.endswith('.playbook'):
                path = os.path.join(subd, f)
                convert_playbook(path, mode, tgt_version)

    # For Converting Test Workflows
    # clear_cache()
    # walkoff.config.paths.db_path = tests.config.test_db_path
    # walkoff.config.paths.case_db_path = tests.config.test_case_db_path
    # walkoff.config.paths.device_db_path = tests.config.test_device_db_path
    # initialize_databases()
    # cache_apps(test_config.test_apps_path)
    # load_app_apis(apps_path=test_config.test_apps_path)
    # for subd, d, files in os.walk(join('tests')):
    #     for f in files:
    #         if f.endswith('.playbook'):
    #             if f not in ['invalidActionWorkflow.playbook', 'invalidAppWorkflow.playbook',
    #                          'invalidInputWorkflow.playbook', 'tooManyActionInputsWorkflow.playbook']:
    #                 path = os.path.join(subd, f)
    #                 convert_playbook(path, mode, tgt_version)


def convert_playbook(path, mode, tgt_version):
    print('Converting {}'.format(path))
    with open(path, 'r+') as f:
        playbook = json.load(f)

        if 'walkoff_version' not in playbook:
            if mode == DOWNGRADE:
                print("Cannot downgrade, no version specified in playbook.")
            elif mode == UPGRADE:
                print("No version specified in playbook, assuming 0.5.0")
                cur_version = "0.5.0"
        else:
            cur_version = playbook['walkoff_version']

        if validate_path(mode, cur_version, tgt_version):
            next_version = ""
            while continue_condition(mode, cur_version, tgt_version) and next_version is not None:

                next_version = get_next_version(mode, cur_version)

                print("{}ing playbook from {} to {}".format(mode[:-1], cur_version, next_version))

                path = "scripts.migrations.workflows."
                if mode == DOWNGRADE:
                    rev = importlib.import_module(path + cur_version.replace(".", "_"))
                    if rev.downgrade_supported:
                        rev.downgrade_playbook(playbook)
                    else:
                        print("Downgrade not supported.")

                elif mode == UPGRADE:
                    rev = importlib.import_module(path + next_version.replace(".", "_"))
                    if rev.upgrade_supported:
                        rev.upgrade_playbook(playbook)
                    else:
                        print("Upgrade not supported.")

                playbook['walkoff_version'] = next_version

                cur_version = next_version

            # f.seek(0)
            # json.dump(playbook, f, sort_keys=True, indent=4, separators=(',', ': '))
            # f.truncate()
