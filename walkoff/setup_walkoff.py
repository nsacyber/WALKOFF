import os

from walkoff.scripts.install_dependencies import install_dependencies
from walkoff.scripts.generate_certificates import generate_certificates


def main():
    print('\nInstalling Python Dependencies...')
    install_dependencies()
    # os.system('pip install -r requirements.txt')
    # os.system('python scripts/install_dependencies.py')

    print('\nGenerating Certificates...')
    generate_certificates()
    # os.system('python scripts/generate_certificates.py')

    # print('\nInstalling Node Packages...')
    # os.chdir('./walkoff/client')
    # os.system('npm install')
    #
    # print('\nCompiling TypeScript Files...')
    # os.system('npm run build')


if __name__ == '__main__':
    main()
