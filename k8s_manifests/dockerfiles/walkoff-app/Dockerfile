# Use an official Python runtime as a parent image
FROM alpine:3.6

WORKDIR /app

RUN apk update && apk upgrade
RUN apk --no-cache add \
    python3 \
    python3-dev \
    build-base \
    postgresql-dev \
    bash \
    git \
    libffi \
    libffi-dev \
    linux-headers

# Setup Python Environment
RUN  if [[ ! -e /usr/bin/python ]];        then ln -sf /usr/bin/python3 /usr/bin/python; fi \
  && if [[ ! -e /usr/bin/python-config ]]; then ln -sf /usr/bin/python3-config /usr/bin/python-config; fi \
  && if [[ ! -e /usr/bin/pydoc ]];         then ln -sf /usr/bin/pydoc3 /usr/bin/pydoc; fi \
  && if [[ ! -e /usr/bin/easy_install ]];  then ln -sf $(ls /usr/bin/easy_install*) /usr/bin/easy_install; fi

RUN easy_install pip \
  && pip install --upgrade pip \
  && if [[ ! -e /usr/bin/pip ]]; then ln -sf /usr/bin/pip3 /usr/bin/pip; fi

RUN git clone -b k8s_development --single-branch --progress --verbose https://www.github.com/nsacyber/WALKOFF.git ./walkoff

WORKDIR /app/walkoff

# Set branch to before receiver separation for 1.0 proof of concept
# RUN git reset --hard 0a779cfaeda15782877b67c89389b223378b2fbd

RUN pip install redis
RUN pip install psycopg2
RUN python setup_walkoff.py

COPY [ "./update_config.py", "/app/walkoff/" ]
COPY [ "./common/app.py", "/app/walkoff/apps/HelloWorld" ]
COPY [ "./common/dist", "/app/walkoff/walkoff/client/dist" ]
COPY [ "./common/node_modules", "/app/walkoff/walkoff/client/node_modules" ]

RUN python update_config.py

EXPOSE 8080 5556 5557

CMD python walkoff.py -a -c data/walkoff.config
