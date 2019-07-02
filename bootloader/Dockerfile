FROM python:3.7-alpine as base

FROM base as builder
RUN apk --no-cache add --update alpine-sdk

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt


FROM base

COPY --from=builder /install /usr/local
COPY ./bootloader.py /app/bootloader.py

WORKDIR /app

ENTRYPOINT ["python", "bootloader.py"]