FROM python:3.7.4-slim-buster as base

# Stage - Install/build Python dependencies
FROM base as builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends autoconf g++ python3.7-dev \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /install
WORKDIR /install

COPY ./api_gateway/requirements.txt /requirements.txt
RUN pip install --no-warn-script-location --prefix="/install" -r /requirements.txt

# Stage - Copy pip packages and source files
FROM base

COPY --from=builder /install /usr/local
COPY ./common /app/common
COPY ./api_gateway /app/api_gateway
WORKDIR /app

CMD gunicorn -k gevent -b $IP:$PORT api_gateway.walkoff:app
