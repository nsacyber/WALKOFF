import os


def main():
    print('\nInstalling Python Dependencies...')
    os.system('pip install -r requirements.txt')
    os.system('python scripts/install_dependencies.py')

    print('\nGenerating Certificates...')
    os.system('python scripts/generate_certificates.py')

    print('\nInstalling Node Packages...')
    os.chdir('./walkoff/client')
    os.system('npm install')

    print('\nCompiling TypeScript Files...')
    os.system('npm run build')


if __name__ == '__main__':
    main()
