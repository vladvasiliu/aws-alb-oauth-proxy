FROM python:3.7.3-alpine3.9 AS builder

LABEL version="0.9"
LABEL description="AWS ALB OAuth Proxy"
LABEL maintainer="Vlad Vasiliu <vladvasiliun@yahoo.fr>"

ARG PROXY_PORT=8080
ARG MON_PORT=8081
EXPOSE $PROXY_PORT
EXPOSE $MON_PORT


RUN apk add --no-cache --virtual build-dependencies \
                                 build-base \
                                 libffi-dev \
                                 openssl-dev
COPY    requirements.txt /
RUN     pip install virtualenv && \
        virtualenv /venv && \
        source /venv/bin/activate && \
        pip install -r /requirements.txt
COPY    aws_alb_oauth_proxy /venv/aws_alb_oauth_proxy


FROM python:3.7.3-alpine3.9
COPY --from=builder /venv /venv

ENTRYPOINT ["/venv/bin/python", "/venv/aws_alb_oauth_proxy"]
