FROM 127.0.0.1:5000/walkoff_app_sdk as base

FROM base as builder

RUN mkdir /install
WORKDIR /install

RUN apk add --update gcc libffi-dev musl-dev linux-headers libressl-dev openssl-dev

COPY requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY src /app

WORKDIR /app

CMD python app.py --log-level DEBUG
