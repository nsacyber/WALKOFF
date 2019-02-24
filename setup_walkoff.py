import os


def main():
    print('\nInstalling Python Dependencies...')
    os.system('pip install -r requirements.txt')
    os.system('python3 scripts/install_dependencies.py')

    print('\nGenerating Certificates...')
    os.system('python3 scripts/generate_certificates.py')

if __name__ == '__main__':
    main()
