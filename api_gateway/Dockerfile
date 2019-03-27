FROM python:3.7-alpine3.8 as base

FROM base as builder
RUN apk --no-cache add --update alpine-sdk libffi libffi-dev postgresql-dev musl-dev

RUN mkdir /install
WORKDIR /install

COPY ./api_gateway/requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
RUN apk --no-cache add --update libpq
COPY ./ /app
WORKDIR /app


CMD gunicorn --reload -t 999999999 -k gevent -b $IP:$PORT api_gateway.walkoff:app
