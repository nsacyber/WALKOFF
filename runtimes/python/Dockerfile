FROM python:3.6-alpine

# Removing unneeded Python stdlib
RUN rm -r /usr/local/lib/python*/ensurepip                    && \
    rm -r /usr/local/lib/python*/lib2to3                      && \
    rm -r /usr/local/lib/python*/turtledemo                   && \
    rm -r /usr/local/lib/python*/idlelib                      && \
    rm -r /usr/local/lib/python*/tkinter                      && \
    rm -r /usr/local/lib/python*/unittest                     && \
    rm /usr/local/lib/python*/turtle.py                       && \
    rm /usr/local/lib/python*/antigravity.py                  && \
    rm /usr/local/lib/python*/webbrowser.py                   && \
    rm /usr/local/lib/python*/doctest.py                      && \
    rm /usr/local/lib/python*/this.py                         && \
    rm /usr/local/lib/python*/pydoc.py

#Update the image
RUN apk --update --no-cache --virtual .build-dep add build-base linux-headers

# Move the requirements into the base
#TODO: Walkoff should in in the requirements.txt
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir cython
RUN pip install --no-cache-dir -r /requirements.txt

# Remove cached files
RUN find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + \
    && runDeps="$( \
        scanelf --needed --nobanner --recursive /usr/local \
                | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                | sort -u \
                | xargs -r apk info --installed \
                | sort -u \
    )" \
    && apk add --virtual .rundeps $runDeps \
    && apk del .build-dep

RUN rm -rf /root/.cache /var/cache /usr/share/terminfo

COPY syncruntime.py /app/syncruntime.py
COPY api.yaml /app/api.yaml
COPY walkoff_schema.json /app/walkoff_schema.json
COPY testapp/HelloWorld /app/app/HelloWorld

WORKDIR /app

EXPOSE 8081

CMD ["uwsgi --http :8081 --wsgi-file syncruntime.py"]