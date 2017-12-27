import logging
import os

from walkoff.config import paths

logger = logging.getLogger(__name__)


def read_and_indent(filename, indent):
    indent = '  ' * indent
    with open(filename, 'r') as file_open:
        return ['{0}{1}'.format(indent, line) for line in file_open]


def compose_api():
    with open(os.path.join(paths.api_path, 'api.yaml'), 'r') as api_yaml:
        final_yaml = []
        for line_num, line in enumerate(api_yaml):
            if line.lstrip().startswith('$ref:'):
                split_line = line.split('$ref:')
                reference = split_line[1].strip()
                indentation = split_line[0].count('  ')
                try:
                    final_yaml.extend(read_and_indent(os.path.join(paths.api_path, reference), indentation))
                    final_yaml.append(os.linesep)
                except (IOError, OSError):
                    logger.error('Could not find or open referenced YAML file {0} in line {1}'.format(reference,
                                                                                                      line_num))
            else:
                final_yaml.append(line)
    with open(os.path.join(paths.api_path, 'composed_api.yaml'), 'w') as composed_yaml:
        composed_yaml.writelines(final_yaml)


if __name__ == '__main__':
    compose_api()
