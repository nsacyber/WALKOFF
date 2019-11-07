FROM python:3.7.4-slim-buster as base

# Stage - Install/build Python dependencies
FROM base as builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends autoconf g++ python3.7-dev \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
COPY ./api/requirements.txt /api_requirements.txt
COPY ./testing/requirements.txt /test_requirements.txt
RUN pip install --no-warn-script-location --prefix="/install" -r /requirements.txt
RUN pip install --no-warn-script-location --prefix="/install" -r /api_requirements.txt
RUN pip install --no-warn-script-location --prefix="/install" -r /test_requirements.txt

# Stage - Copy pip packages and source files
FROM base

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    apt-transport-https ca-certificates curl gnupg2 software-properties-common \
 && apt-key adv --fetch-keys https://download.docker.com/linux/debian/gpg \
 && add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
 && apt-get update \
 && apt-get install -y --no-install-recommends docker-ce-cli \
 && rm -rf /var/lib/apt/lists/*


COPY --from=builder /install /usr/local
COPY ./api /app/api
COPY ./app_sdk /app/app_sdk
COPY ./apps /app/apps
COPY ./bootloader /app/bootloader
COPY ./common /app/common
COPY ./data /app/data
COPY ./docs /app/docs
COPY ./nginx /app/nginx
COPY ./socketio /app/socketio
COPY ./testing /app/testing
COPY ./umpire /app/umpire
COPY ./worker /app/worker
COPY ./walkoff.sh /app/walkoff.sh

WORKDIR /app

CMD pytest --cov=api testing/api
