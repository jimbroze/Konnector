#!/bin/bash

# docker build -t konnector .

docker run -d --name konnector \
    -p 8080:8080 \
    -e PORT=8080 \
    -e MODULE_NAME=konnector.main \
    -e LOG_LEVEL=debug \
    -e AUTH=false \
    --health-cmd="curl --fail -I -X GET http://localhost:8080 || exit 1" \
    --health-interval=30s \
    --health-retries=5 \
    --health-start-period=30s \
    --health-timeout=5s \
    --restart unless-stopped \
    --log-driver loki \
    --log-opt loki-url="http://localhost:3100/loki/api/v1/push" \
    konnector