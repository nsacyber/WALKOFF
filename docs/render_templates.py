from pkgutil import iter_modules
from jinja2 import Environment, FileSystemLoader
from os import path, sep, listdir

automodule_directive = '''
.. automodule:: {module_name}
   :members:
'''


def generate_module_autodocs(module_prefix):
    module_path = path.join('..',  module_prefix.replace('.', sep))
    modules = [automodule_directive.format(module_name=module_prefix)]
    submodules = [automodule_directive.format(module_name='{}.{}'.format(module_prefix, module_name))
                  for _, module_name, _ in iter_modules([module_path])]
    modules.extend(submodules)
    return '\n\n'.join(modules)


if __name__ == '__main__':
    import sys
    sys.path.append('..')
    env = Environment(loader=FileSystemLoader('templates'))
    env.globals.update(generate_module_autodocs=generate_module_autodocs)
    for template in listdir('templates'):
        with open(template, 'w') as output_template:
            output_template.write(env.get_template(template).render())
