

def register_blueprints():
    from server import app
    from server.blueprints import app as appblueprint
    from server.blueprints import widget, playbook, cases, configuration, users, roles, trigger, scheduler
    app.register_blueprint(widget.widget_page, url_prefix='/apps/<app>/<widget>')
    app.register_blueprint(appblueprint.app_page, url_prefix='/apps/<app>')
    app.register_blueprint(playbook.playbook_page, url_prefix='/playbook')
    app.register_blueprint(cases.cases_page, url_prefix='/cases')
    app.register_blueprint(configuration.configurations_page, url_prefix='/configuration')
    app.register_blueprint(users.users_page, url_prefix='/users')
    app.register_blueprint(roles.roles_page, url_prefix='/roles')
    app.register_blueprint(trigger.triggers_page, url_prefix='/execution/listener')
    app.register_blueprint(scheduler.scheduler_page, url_prefix='/execution/scheduler')
    __register_all_app_blueprints()


class AppBlueprint(object):
    def __init__(self, blueprint, rule=''):
        self.blueprint = blueprint
        self.rule = rule


def __register_all_app_blueprints():
    from importlib import import_module
    from core.helpers import import_submodules
    import apps
    from server import app as flaskapp
    imported_apps = import_submodules(apps)
    for app_name, app_module in imported_apps.items():
        try:
            import_module('{0}.display'.format(app_name))
            display_module = getattr(app_module, 'display')
            blueprints = [getattr(display_module, field)
                          for field in dir(display_module) if (not field.startswith('__')
                                                               and isinstance(getattr(display_module, field),
                                                                              AppBlueprint))]
            app_name = app_name.split('.')[-1]
            url_prefix = '/apps/{0}'.format(app_name)
            for blueprint in blueprints:
                rule = '{0}{1}'.format(url_prefix, blueprint.rule) if blueprint.rule else url_prefix
                flaskapp.register_blueprint(blueprint.blueprint, url_prefix=rule)
        except ImportError:
            pass
