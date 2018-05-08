import os
import argparse
import subprocess


def local_install():
    subprocess.call(["pip", "install", "-r", "requirements.txt"])

    from scripts.install_dependencies import install_dependencies
    from scripts.generate_certificates import generate_certificates
    from config import Config

    print('\nInstalling Python Dependencies...')
    install_dependencies()

    print('\nGenerating Certificates...')
    generate_certificates()

    print('\nInstalling Node Packages...')
    os.chdir(Config.CLIENT_PATH)
    os.system('npm install')

    print('\nCompiling TypeScript Files...')
    os.system('npm run build')


def pip_install():
    subprocess.call(["pip", "install", "-r", "requirements.txt"])

    from walkoff.scripts.install_dependencies import install_dependencies
    from walkoff.scripts.generate_certificates import generate_certificates
    from walkoff.set_paths import main as set_paths_main
    from walkoff.config import Config

    set_paths_main()

    print('\nInstalling Python Dependencies...')
    install_dependencies()

    print('\nGenerating Certificates...')
    generate_certificates()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--localinstall",
                        help="Use if WALKOFF was downloaded via Git rather than pip. "
                             "Will use existing app, interface, data directories and will download Node modules",
                        action="store_true")

    args = parser.parse_args()

    if args.localinstall:
        local_install()

    else:
        if not os.path.isfile(os.path.join('.', 'walkoff', 'walkoff_external.tar.gz')):
            print("Could not find walkoff_external archive.\n"
                  "If you downloaded this from Github, run python walkoff/setup_walkoff.py --localinstall\n"
                  "This will use the existing apps, interfaces, and data directories.")
        else:
            pip_install()


if __name__ == '__main__':
    main()
