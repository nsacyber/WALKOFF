import json
import os
from flask import Blueprint, request, Response, current_app
from flask_security import auth_token_required, roles_accepted
import core.case.database as case_database
import core.case.subscription as case_subscription
from server import forms
from core.case.subscription import CaseSubscriptions, add_cases, delete_cases, \
    rename_case
import core.config.config
import core.config.paths
from core.helpers import construct_workflow_name_key
from gevent.event import Event, AsyncResult
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED


def display_cases():
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        return case_database.case_db.cases_as_json()
    return __func()


def add_case(case):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        case_obj = CaseSubscriptions()
        add_cases({"{0}".format(str(case)): case_obj})
        case_obj = running_context.CaseSubscription.query.filter_by(name=case).first()
        if not case_obj:
            running_context.db.session.add(running_context.CaseSubscription(name=case))
            running_context.db.session.commit()
            current_app.logger.debug('Case added: {0}'.format(case))
        return case_subscription.subscriptions_as_json()
    return __func()


def get_case(case):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        case_obj = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == case).first()
        if case_obj:
            return {'case': case_obj.as_json()}
        else:
            return {'status': 'Case with given name does not exist'}
    return __func()


def edit_case(case):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        form = forms.EditCaseForm(request.form)
        if form.validate():
            if form.name.data:
                rename_case(case, form.name.data)
                case_obj = running_context.CaseSubscription.query.filter_by(name=case).first()
                if case_obj:
                    case_obj.name = form.name.data
                    running_context.db.session.commit()

                if form.note.data:
                    case_database.case_db.edit_case_note(form.name.data, form.note.data)
                current_app.logger.debug('Case name changed from {0} to {1}'.format(case, form.name.data))
            elif form.note.data:
                case_database.case_db.edit_case_note(case, form.note.data)
            return case_database.case_db.cases_as_json()
    return __func()


def delete_case(case):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        delete_cases([case])
        case_obj = running_context.CaseSubscription.query.filter_by(name=case).first()
        if case_obj:
            running_context.db.session.delete(case_obj)
            running_context.db.session.commit()
            current_app.logger.debug('Case deleted {0}'.format(case))
        return case_subscription.subscriptions_as_json()
    return __func()


def import_cases():
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        form = forms.ImportCaseForm(request.form)
        filename = form.filename.data if form.filename.data else core.config.paths.default_case_export_path
        if os.path.isfile(filename):
            try:
                with open(filename, 'r') as cases_file:
                    cases_file = cases_file.read()
                    cases_file = cases_file.replace('\n', '')
                    cases = json.loads(cases_file)
                case_subscription.add_cases(cases)
                for case in cases.keys():
                    running_context.db.session.add(running_context.CaseSubscription(name=case))
                    running_context.CaseSubscription.update(case)
                    running_context.db.session.commit()
                return {"status": "success", "cases": case_subscription.subscriptions_as_json()}
            except (OSError, IOError) as e:
                current_app.logger.error('Error importing cases from file {0}: {1}'.format(filename, e))
                return {"status": "error reading file"}
            except ValueError as e:
                current_app.logger.error('Error importing cases from file {0}: Invalid JSON {1}'.format(filename, e))
                return {"status": "file contains invalid JSON"}
        else:
            current_app.logger.debug('Cases successfully imported from {0}'.format(filename))
            return {"status": "error: file does not exist"}
    return __func()
