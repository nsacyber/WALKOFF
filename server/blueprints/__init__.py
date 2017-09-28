
class _BlueprintInjection(object):
    def __init__(self, blueprint, rule=''):
        self.blueprint = blueprint
        self.rule = rule

AppBlueprint = _BlueprintInjection
WidgetBlueprint = _BlueprintInjection
