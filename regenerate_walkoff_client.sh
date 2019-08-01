#!/bin/zsh

python generate_client_openapi.py

docker run --rm -v ${PWD}:/local openapitools/openapi-generator-cli generate \
    -i /local/api_gateway/api/client_api.yaml \
    -g python \
    -o /local/common/walkoff_client \
    --package-name walkoff_client \

pip uninstall --yes walkoff_client
pip install common/walkoff_client
