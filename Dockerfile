FROM python:3.7.3-alpine3.9 AS builder

LABEL version="0.9"
LABEL description="AWS ALB OAuth Proxy"
LABEL maintainer="Vlad Vasiliu <vladvasiliun@yahoo.fr>"

ARG PROXY_PORT=8080
ARG MON_PORT=8081
EXPOSE $PROXY_PORT
EXPOSE $MON_PORT

RUN     pip install virtualenv && \
        virtualenv /venv && \
        source /venv/bin/activate
COPY    requirements.txt /
COPY    aws_alb_oauth_proxy /venv/

RUN apk add --no-cache --virtual build-dependencies \
                                 build-base \
                                 libffi-dev \
                                 openssl-dev
RUN pip install -r /requirements.txt


FROM python:3.7.3-alpine3.9
COPY --from=builder /venv /venv

ENTRYPOINT ["python", "/aws_alb_oauth_proxy"]