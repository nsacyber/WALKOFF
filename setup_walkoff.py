import os


def main():
    print('\nInstalling Python Dependencies...')
    os.system('pip install -r requirements.txt')
    os.system('python scripts/install_dependencies.py')

    print('\nGenerating Certificates...')
    os.system('python scripts/generate_certificates.py')

    print('\nInstalling Node Packages...')
    os.chdir('./client')
    os.system('npm install')

    print('\nInstalling Gulp...')
    os.system('npm install gulp-cli -g')

    print('\nGulping TypeScript Files...')
    os.system('gulp ts')


if __name__ == '__main__':
    main()
