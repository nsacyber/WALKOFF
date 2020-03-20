FROM python:3.7.4-slim-buster as base

# Stage - Install/build Python dependencies
FROM base as builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    autoconf g++ \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /install
WORKDIR /install

COPY bootloader/requirements.txt /requirements.txt
RUN pip install --no-warn-script-location --prefix="/install" -r /requirements.txt

# Stage - Copy pip packages and source files
FROM base

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    apt-transport-https ca-certificates curl gnupg2 software-properties-common \
 && apt-key adv --fetch-keys https://download.docker.com/linux/debian/gpg \
 && add-apt-repository "deb https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
 && apt-get update \
 && apt-get install -y --no-install-recommends docker-ce-cli \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
#COPY ./.dockerignore /app/.dockerignore
#COPY ./bootloader/ /app/bootloader
#COPY ./common /app/common
#WORKDIR /app

ENTRYPOINT ["python", "-m", "bootloader.bootloader"]

