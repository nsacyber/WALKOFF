FROM node:12.13.0-buster-slim as base

# Stage - Install/build Python dependencies
FROM base as builder

RUN mkdir /install
WORKDIR /install

COPY ./socketio /install
RUN npm install
RUN npm run build

# Stage - Copy pip packages and source files
FROM base

COPY --from=builder /install /
# COPY ./common /app/common
# COPY ./api /app/api
# WORKDIR /dist

EXPOSE 3000
CMD [ "npm", "start" ]