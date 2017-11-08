from apps import Event
from interfaces import AppBlueprint
from flask import Blueprint

blueprint = AppBlueprint(blueprint=Blueprint('UtilitiesPage', __name__))

wait = Event('Wait')


@blueprint.blueprint.route('/resume')
def resume():
    wait.trigger(None)

