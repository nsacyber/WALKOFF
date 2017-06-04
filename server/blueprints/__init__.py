

class _BlueprintInjection(object):
    def __init__(self, blueprint, rule=''):
        self.blueprint = blueprint
        self.rule = rule

AppBlueprint = _BlueprintInjection
WidgetBlueprint = _BlueprintInjection


def register_blueprints(flaskapp):
    from server.blueprints import app as app
    from server.blueprints import widget, events, widgets, workflowresult
    flaskapp.register_blueprint(app.app_page, url_prefix='/apps/<app>')
    flaskapp.register_blueprint(widget.widget_page, url_prefix='/apps/<app>/<widget>')
    flaskapp.register_blueprint(widgets.widgets_page, url_prefix='/apps/<app>/widgets/<widget>')
    flaskapp.register_blueprint(events.events_page, url_prefix='/events')
    flaskapp.register_blueprint(workflowresult.workflowresults_page, url_prefix='/workflowresults')
    __register_all_app_blueprints(flaskapp)


def __get_blueprints_in_module(module, sub_module_name='display'):
    from importlib import import_module
    import_module('{0}.{1}'.format(module.__name__, sub_module_name))
    display_module = getattr(module, sub_module_name)
    blueprints = [getattr(display_module, field)
                  for field in dir(display_module) if (not field.startswith('__')
                                                       and isinstance(getattr(display_module, field),
                                                                      _BlueprintInjection))]
    return blueprints


def __register_app_blueprint(flaskapp, blueprint, url_prefix):
    rule = '{0}{1}'.format(url_prefix, blueprint.rule) if blueprint.rule else url_prefix
    flaskapp.register_blueprint(blueprint.blueprint, url_prefix=rule)


def __register_all_app_blueprints(flaskapp):
    from core.helpers import import_submodules
    import apps
    imported_apps = import_submodules(apps)
    for app_name, app_module in imported_apps.items():
        try:
            blueprints = __get_blueprints_in_module(app_module)
        except ImportError:
            continue
        else:
            url_prefix = '/apps/{0}'.format(app_name.split('.')[-1])
            for blueprint in blueprints:
                __register_app_blueprint(flaskapp, blueprint, url_prefix)

            __register_all_app_widget_blueprints(flaskapp, app_module)


def __register_all_app_widget_blueprints(flaskapp, app_module):
    from importlib import import_module
    from core.helpers import import_submodules
    try:
        widgets_module = import_module('{0}.widgets'.format(app_module.__name__))
    except ImportError:
        return
    else:
        app_name = app_module.__name__.split('.')[-1]
        imported_widgets = import_submodules(widgets_module)
        for widget_name, widget_module in imported_widgets.items():
            try:
                blueprints = __get_blueprints_in_module(widget_module)
            except ImportError:
                continue
            else:
                url_prefix = '/apps/{0}/{1}'.format(app_name, widget_name.split('.')[-1])
                for blueprint in blueprints:
                    __register_app_blueprint(flaskapp, blueprint, url_prefix)






