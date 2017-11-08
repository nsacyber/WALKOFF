import os


def convert_apis():
    for subdir, dir, files in os.walk('./apps'):
        for file in (file for file in files if file == 'api.yaml'):
            print('Processing {0}/{1}'.format(subdir, file))
            with open(os.path.join(subdir, file), 'r') as f:
                api = f.read()
                api = api.replace('externalDocs:', 'external_docs:')
                api = api.replace('termsOfService:', 'terms_of_service:')
                api = api.replace('dataIn:', 'data_in:')
            with open(os.path.join(subdir, file), 'w') as f:
                f.write(api)


if __name__ == "__main__":
    convert_apis()