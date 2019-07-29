FROM python:3.7-alpine as base

FROM base as builder
RUN apk --no-cache add --update alpine-sdk

RUN mkdir /install
WORKDIR /install

COPY ./umpire/requirements.txt /requirements.txt
RUN git clone "https://github.com/aio-libs/aioredis.git"
RUN pip install --prefix="/install" ./aioredis
RUN pip install --prefix="/install" ./aioredis
RUN pip install --prefix="/install" --no-deps asteval
RUN pip install --prefix="/install" six
RUN pip install --prefix="/install" -r /requirements.txt


FROM base

COPY --from=builder /install /usr/local
COPY ./app_sdk /app/app_sdk
COPY ./worker /app/worker
COPY ./common /app/common
COPY ./umpire /app/umpire

WORKDIR /app

CMD python -m umpire.umpire