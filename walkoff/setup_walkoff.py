import os
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--development",
                        help="Dev mode - assume not installed via pip, and build node packages",
                        action="store_true")

    args = parser.parse_args()

    if args.development:
        os.system('python walkoff/set_paths.py')

        print('\nInstalling Python Dependencies...')
        os.system('pip install -r requirements.txt')
        os.system('python walkoff/scripts/install_dependencies.py')
        print('\nGenerating Certificates...')
        os.system('python walkoff/scripts/generate_certificates.py')

        print('\nInstalling Node Packages...')
        os.chdir(Config.CLIENT_PATH)
        os.chdir('walkoff/client')
        os.system('npm install')

        print('\nCompiling TypeScript Files...')
        os.system('npm run build')

    else:
        from walkoff.scripts.install_dependencies import install_dependencies
        from walkoff.scripts.generate_certificates import generate_certificates
        from walkoff.set_paths import main as set_paths_main
        from walkoff.config import Config

        set_paths_main()

        print('\nInstalling Python Dependencies...')
        install_dependencies()

        print('\nGenerating Certificates...')
        generate_certificates()


if __name__ == '__main__':
    main()
