FROM python:3.7-alpine as base

FROM base as builder
RUN apk --no-cache add --update alpine-sdk

RUN mkdir /install
WORKDIR /install

COPY ./listener/requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt

COPY ./listener /app/listener
WORKDIR /app

COPY --from=builder /install /usr/local
COPY ./common /app/common

CMD python listener.py