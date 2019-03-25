FROM walkoff_app_sdk as base

FROM base as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY src /app
COPY src/common /app
COPY src/app_sdk /app

WORKDIR /app

CMD python app.py --log-level DEBUG
