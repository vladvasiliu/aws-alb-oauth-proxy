import asyncio
import logging
from typing import Mapping

import jwt
from aiohttp import ClientSession, web, DummyCookieJar
from aiohttp.web_exceptions import HTTPUnauthorized, HTTPProxyAuthenticationRequired, HTTPBadRequest
from jwt import DecodeError, ExpiredSignatureError
from yarl import URL

from helpers import clean_response_headers
from monitoring import REQUEST_HISTOGRAM, UPSTREAM_STATUS_COUNTER

logger = logging.getLogger(__name__)


class Proxy:
    """This is basically a reverse proxy that translates some headers. We don't care about cookies or sessions.

    This takes the OIDC data from the load balancer, validates it, and adds new headers as expected by Grafana.
    Some form of key caching may be useful and will be implemented later.
    """

    def __init__(
        self,
        upstream: str,
        aws_region: str,
        header_name: str = "X-WEBAUTH-USER",
        header_property: str = "email",
        ignore_auth: bool = False,
    ):
        """Creates a server for a given AWS region.

        :param upstream: The URL of the upstream server
        :param aws_region: There AWS region where this is running, used to fetch the key.
        :param header_name: HTTP header name to send, as configured in ``grafana.ini``.
        :param header_property: The header property to use from the payload. Should match what Grafana expects.
        :param ignore_auth: Whether to run without authentication. Should only be used in testing.
        """
        self._ignore_auth = ignore_auth
        self._upstream = URL(upstream)
        self._key_url = URL(f"https://public-keys.auth.elb.{aws_region}.amazonaws.com")
        self._header_name = header_name
        self._header_property = header_property

    async def _setup_session(self, app):
        """Handle context sessions nicely.

        `See docs <https://docs.aiohttp.org/en/latest/client_advanced.html#persistent-session>`_"""
        self._key_session = ClientSession(raise_for_status=True)
        self._upstream_session = ClientSession(
            raise_for_status=False, cookie_jar=DummyCookieJar(), auto_decompress=False
        )
        yield
        await asyncio.gather(self._key_session.close(), self._upstream_session.close())

    def runner(self):
        app = web.Application(middlewares=[self.auth_middleware], logger=logger)
        app.router.add_route("*", "/{tail:.*}", self.handle_request)
        app.cleanup_ctx.append(self._setup_session)
        return web.AppRunner(app)

    async def _decode_payload(self, oidc_data: str) -> Mapping[str, str]:
        """ Returns the payload of the OIDC data sent by the ALB

        `Relevant AWS Documentation
        <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html#user-claims-encoding>`_

        :param oidc_data: OIDC data from alb
        :return: payload
        :raise: jwt.exceptions.ExpiredSignatureError: If the token is not longer valid
        """
        header = jwt.get_unverified_header(oidc_data)
        kid = header["kid"]
        alg = header["alg"]

        async with self._key_session.get(self._key_url.join(URL(kid))) as response:
            pub_key = await response.text()

        payload = jwt.decode(oidc_data, pub_key, algorithms=[alg])
        try:
            return payload[self._header_property]
        except KeyError:
            logger.warning(f"Could not find '{self._header_property}' key in OIDC Data.")
            raise HTTPBadRequest

    async def _add_auth_info(self, request: web.Request):
        """Adds the authentication information, if any, to the request.

        Catches exceptions from decoding the payload and converts them to HTTP exceptions to be propagated.
        If authentication is disabled via :attr:`~_ignore_auth` doesn't do anything.

        Headers are kept in a `CIMultiDictProxy`_ so case of the header is not important.

        .. _CIMultiDictProxy: https://multidict.readthedocs.io/en/stable/multidict.html#multidict.CIMultiDictProxy
        """
        if self._ignore_auth:
            return None

        try:
            oidc_data = request.headers["X-Amzn-Oidc-Data"]
        except KeyError:
            logger.warning("No 'X-Amzn-Oidc-Data' header present. Dropping request.")
            raise HTTPProxyAuthenticationRequired()
        try:
            request["auth_payload"] = (self._header_name, await self._decode_payload(oidc_data))
        except ExpiredSignatureError:
            logger.warning("Got expired token. Dropping request.")
            raise HTTPUnauthorized()
        except DecodeError as e:
            logger.warning("Couldn't decode token. Dropping request.")
            logger.debug("Couldn't decode token: %s" % e)
            raise HTTPBadRequest()

    @REQUEST_HISTOGRAM.time()
    async def handle_request(self, request: web.Request) -> web.StreamResponse:
        upstream_url = self._upstream.join(request.url.relative())
        upstream_request = self._upstream_session.request(
            url=upstream_url,
            method=request.method,
            headers=clean_response_headers(request),
            params=request.query,
            data=request.content,
            allow_redirects=False,
        )
        async with upstream_request as upstream_response:
            UPSTREAM_STATUS_COUNTER.labels(method=upstream_response.method, status=upstream_response.status).inc()
            response = web.StreamResponse(status=upstream_response.status, headers=upstream_response.headers)
            await response.prepare(request)
            async for data in upstream_response.content.iter_any():
                await response.write(data)
            await response.write_eof()
            return response

    @web.middleware
    async def auth_middleware(self, request, handler):
        await self._add_auth_info(request)
        return await handler(request)
