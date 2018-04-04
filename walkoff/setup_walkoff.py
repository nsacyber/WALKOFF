import os

# from walkoff.scripts.install_dependencies import install_dependencies
# from walkoff.scripts.generate_certificates import generate_certificates
# from walkoff.set_paths import main as set_paths_main
# from walkoff.config import Config


def main():

    # set_paths_main()
    os.system('python walkoff/set_paths.py')

    print('\nInstalling Python Dependencies...')
    # install_dependencies()
    os.system('pip install -r requirements.txt')
    os.system('python walkoff/scripts/install_dependencies.py')

    print('\nGenerating Certificates...')
    # generate_certificates()
    os.system('python walkoff/scripts/generate_certificates.py')

    print('\nInstalling Node Packages...')
    # os.chdir(Config.CLIENT_PATH)
    os.chdir('walkoff/client')
    os.system('npm install')

    print('\nCompiling TypeScript Files...')
    os.system('npm run build')


if __name__ == '__main__':
    main()
