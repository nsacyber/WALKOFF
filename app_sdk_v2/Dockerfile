FROM golang:latest as base

# Stage - Install/build golang walkoff_app_sdk
FROM base as builder
ENV GOPATH /go
ENV PATH $GOPATH/bin:/usr/local/go/bin:$PATH
RUN mkdir -p "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH"

RUN go get github.com/fsnotify/fsnotify
RUN go get github.com/go-redis/redis
COPY ./app_sdk_v2/walkoff_app_sdk /app/walkoff_app_sdk
RUN go build -o /walkoff_app_sdk/action.exe /app/walkoff_app_sdk/action/action.go
RUN go build -o /walkoff_app_sdk/agent.exe /app/walkoff_app_sdk/agent.go

# Stage - Copy executable
FROM base
COPY --from=builder /walkoff_app_sdk /app/walkoff_app_sdk

# No CMD/ENTRYPOINT because this image should never run alone