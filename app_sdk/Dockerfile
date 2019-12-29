FROM python:3.7.4-slim-buster as base

# Stage - Install/build Python dependencies
FROM base as builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends git autoconf g++ libffi-dev libssl-dev \
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
COPY ./app_sdk/walkoff_app_sdk /app/walkoff_app_sdk
COPY ./common /app/common

# No CMD/ENTRYPOINT because this image should never run alone
