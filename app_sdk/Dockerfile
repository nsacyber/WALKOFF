FROM python:3.7-alpine as base

FROM base as builder
RUN apk --no-cache add --update alpine-sdk libffi libffi-dev musl-dev openssl-dev

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN git clone "https://github.com/aio-libs/aioredis.git"
RUN pip install --prefix="/install" ./aioredis
RUN pip install --prefix="/install" --no-deps asteval
RUN pip install --prefix="/install" six
RUN pip install --prefix="/install" -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY walkoff_app_sdk/__init__.py /app/walkoff_app_sdk/__init__.py
COPY walkoff_app_sdk/app_base.py /app/walkoff_app_sdk/app_base.py
COPY walkoff_app_sdk/common /app/walkoff_app_sdk/common