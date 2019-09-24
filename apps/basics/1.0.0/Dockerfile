# Use the Walkoff App SDK as a base image
FROM python:3.7.4-slim-buster as base

# Stage - Install/build Python dependencies
FROM base as builder

# Install pip packages to a temporary directory for copying into the final image later
RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install --no-warn-script-location --prefix="/install" -r /requirements.txt

# Stage - Copy pip packages and source files
FROM base

COPY --from=127.0.0.1:5000/walkoff_app_sdk_v2 /usr/local /usr/local
COPY --from=127.0.0.1:5000/walkoff_app_sdk_v2 /app /app
COPY --from=builder /install /usr/local
COPY src /app

# Finally, set the working directory and how our app will run.
WORKDIR /app
CMD walkoff_app_sdk/agent.exe