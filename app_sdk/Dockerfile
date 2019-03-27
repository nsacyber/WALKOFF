FROM python:3.7-alpine as base

FROM base as walkoff_app_sdk
RUN apk --no-cache add --update alpine-sdk

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install --prefix="/install" --no-deps asteval
RUN pip install --prefix="/install" six
RUN pip install --prefix="/install" -r /requirements.txt

FROM base

COPY --from=walkoff_app_sdk /install /usr/local
COPY walkoff_app_sdk/__init__.py /app/app_sdk/__init__.py
COPY walkoff_app_sdk/app_base.py /app/app_sdk/app_base.py
COPY walkoff_app_sdk/common /app/common

