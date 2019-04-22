FROM python@sha256:8fe3b17b88644d379ca7e0c724a82a595c8cfbe2b37e1d6d33e7bb5c435a8a29 as base

FROM base as builder
RUN apk --no-cache add --update alpine-sdk libffi libffi-dev postgresql-dev musl-dev

RUN mkdir /install
WORKDIR /install

COPY ./api_gateway/requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
RUN apk --no-cache add --update libpq
COPY ./common /app/common
COPY ./api_gateway /app/api_gateway
WORKDIR /app


CMD gunicorn -k gevent -b $IP:$PORT api_gateway.walkoff:app
