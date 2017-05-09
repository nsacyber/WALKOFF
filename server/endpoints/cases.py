import json
import logging
import os
from flask import Blueprint, request, Response, current_app
import core.case.database as case_database

cases_page = Blueprint('cases_page', __name__)


def display_cases():
    def __func():
        return case_database.case_db.cases_as_json()
    return __func()