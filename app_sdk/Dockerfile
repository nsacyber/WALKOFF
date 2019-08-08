FROM python:3.7.4-slim-buster as base

# Stage - Install/build Python dependencies
FROM base as builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends git autoconf g++ \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /install
WORKDIR /install

COPY ./app_sdk/requirements.txt /requirements.txt
RUN pip install --no-warn-script-location --prefix="/install" git+https://github.com/aio-libs/aioredis.git
RUN pip install --no-warn-script-location --prefix="/install" --no-deps asteval
RUN pip install --no-warn-script-location --prefix="/install" -r /requirements.txt

# Stage - Copy pip packages and source files
FROM base

COPY --from=builder /install /usr/local
COPY ./app_sdk/walkoff_app_sdk/__init__.py /app/walkoff_app_sdk/__init__.py
COPY ./app_sdk/walkoff_app_sdk/app_base.py /app/walkoff_app_sdk/app_base.py
COPY ./app_sdk/walkoff_app_sdk/common /app/walkoff_app_sdk/common

# No CMD/ENTRYPOINT because this image should never run alone