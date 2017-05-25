import subprocess
import os.path
import shutil

branch = 'master'
swagger_path = os.path.join('.', 'server', 'api')
api_file = os.path.join('.', 'swagger', 'api.yaml')


def read_and_indent(filename, indent):
    indent = '  '*indent
    with open(filename, 'r') as file_open:
        return ['{0}{1}'.format(indent, line) for line in file_open]


def compose_yamls():
    print('Composing api specification...') 
    with open(os.path.join(swagger_path, 'api.yaml'), 'r') as api_yaml:
        final_yaml = []
        for line_num, line in enumerate(api_yaml):
            if line.lstrip().startswith('$ref:'):
                split_line = line.split('$ref:')
                reference = split_line[1].strip()
                indentation = split_line[0].count('  ')
                try:
                    final_yaml.extend(read_and_indent(os.path.join(swagger_path, reference), indentation))
                    final_yaml.append('\n')
                except (IOError, OSError):
                    print('Could not find or open referenced YAML file {0} in line {1}'.format(reference, line_num))
            else:
                final_yaml.append(line)
    with open(api_file, 'w') as composed_api:
        composed_api.writelines(final_yaml)


def checkout_swagger_yamls():
    api_path = 'server/api'
    print('Checking out most recent api...')
    command = 'git checkout {0} {1}'.format(branch, api_path).split()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    if err:
        print(err)


def cleanup():
    print('Cleaning up...')
    command = 'git rm -rf server'.split()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    if err:
        print(err)

if __name__ == '__main__':
    checkout_swagger_yamls()
    compose_yamls()
    cleanup()
    print('Done!')
