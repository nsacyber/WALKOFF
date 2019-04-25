FROM localhost:5000/walkoff_app_sdk as base

FROM base as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt

RUN apk add nmap

FROM base

COPY --from=builder /install /usr/local
COPY src /app

WORKDIR /app

CMD python app.py --log-level DEBUG
