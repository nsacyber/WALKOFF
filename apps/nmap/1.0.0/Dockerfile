FROM 127.0.0.1:5000/walkoff_app_sdk as base

FROM base as builder

RUN apk --no-cache add --update alpine-sdk libffi libffi-dev musl-dev openssl-dev

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local
COPY src /app

RUN apk --no-cache add --update nmap

WORKDIR /app
CMD python app.py --log-level DEBUG
