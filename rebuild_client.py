import os


def main():
    print('\nInstalling Node Packages...')
    os.chdir('./walkoff/client')
    os.system('npm install')

    print('\nCompiling TypeScript Files...')
    os.system('npm run build:prod')


if __name__ == '__main__':
    main()
