# Use the Walkoff App SDK as a base image
FROM python:3.7.4-slim-buster as base

# Stage - Install/build Python dependencies
FROM base as builder

# Install any OS packages required for building Python dependencies
# Removing package cache reduces final image size since we won't apt-get install anything else in this stage

#RUN apt-get update \
# && apt-get install -y --no-install-recommends git autoconf g++ \
# && rm -rf /var/lib/apt/lists/*

# Install pip packages to a temporary directory for copying into the final image later
RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install --no-warn-script-location --prefix="/install" -r /requirements.txt

# Stage - Copy pip packages and source files
FROM base

COPY --from=127.0.0.1:5000/walkoff_app_sdk /usr/local /usr/local
COPY --from=127.0.0.1:5000/walkoff_app_sdk /app /app
COPY --from=builder /install /usr/local
COPY src /app

# Install any OS packages dependencies needed in the final image for our app to run
# Removing package cache reduces final image size since we won't apt-get install anything else in this stage

RUN apt-get update \
 && apt-get install -y --no-install-recommends nmap \
 && rm -rf /var/lib/apt/lists/*

# Finally, set the working directory and how our app will run.
WORKDIR /app
CMD python app.py --log-level DEBUG
