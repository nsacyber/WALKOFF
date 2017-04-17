

def register_blueprints():
    from server import app as app
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

