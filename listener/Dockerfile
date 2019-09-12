FROM python:3.7.4-slim-buster as base

FROM base as builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends git autoconf g++ \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /install
WORKDIR /install

COPY ./listener/requirements.txt /requirements.txt
RUN pip install --no-warn-script-location --prefix="/install" -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY ./common /app/common
COPY ./listener /app/listener

WORKDIR /app

CMD python -m listener.listener