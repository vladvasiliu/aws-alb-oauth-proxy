FROM python:3.7.3-alpine3.9 AS builder

LABEL version="0.9"
LABEL description="AWS ALB OAuth Proxy"
LABEL maintainer="Vlad Vasiliu <vladvasiliun@yahoo.fr>"

ARG PROXY_PORT=8080
ARG MON_PORT=8081
EXPOSE $PROXY_PORT
EXPOSE $MON_PORT

COPY    requirements.txt /wheels/
WORKDIR /wheels

RUN apk add --no-cache --virtual build-dependencies \
    build-base \
    libffi-dev \
    openssl-dev

RUN pip wheel -r requirements.txt
RUN apk del build-dependencies


FROM python:3.7.3-alpine3.9
COPY --from=builder /wheels /wheels
RUN pip install -r /wheels/requirements.txt -f /wheels && \
    rm -rf /wheels && \
    rm -rf /root/.cache
COPY aws_alb_oauth_proxy /aws_alb_oauth_proxy

ENTRYPOINT ["python", "/aws_alb_oauth_proxy"]