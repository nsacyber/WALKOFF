FROM python:3.7-alpine as base

FROM base as builder
RUN apk --no-cache add --update alpine-sdk

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY src/app_sdk /app/app_sdk
COPY src/app.py /app/

WORKDIR /app

CMD python app.py --log-level DEBUG
#CMD printf "Hello World"
