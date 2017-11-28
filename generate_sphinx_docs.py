import os


def main():
    print('\nGenerating Sphinx documentation...')
    os.system('sphinx-apidoc -o sphinx/core ./core')
    os.system('sphinx-apidoc -o sphinx/server ./server')
    os.system('sphinx-apidoc -o sphinx/apps ./apps')
    os.system('sphinx-apidoc -o sphinx/interfaces ./interfaces')
    os.system('make html')

if __name__ == '__main__':
    main()
