import asyncio
import base64
import json
import logging
from typing import Mapping, Optional

from aiohttp import ClientSession, web
import jwt
from aiohttp.web_exceptions import (
    HTTPUnauthorized,
    HTTPProxyAuthenticationRequired,
    HTTPBadRequest,
)
from jwt import DecodeError, ExpiredSignatureError
from yarl import URL

from helpers import clean_response_headers

logger = logging.getLogger(__name__)


def _kid_from_oidc_data(oidc_data: str) -> (str, str):
    """Returns the key ID and algorithm from AWS OIDC data

    `AWS Documentation
    <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html#user-claims-encoding>`_
    """
    headers = oidc_data.split(".")[0]

    # Get Key ID
    decoded_headers = base64.b64decode(headers).decode("utf-8")
    json_headers = json.loads(decoded_headers)
    return json_headers["kid"], json_headers["alg"]


class Proxy:
    """This is basically a reverse proxy that translates some headers. We don't care about cookies or sessions.

    This takes the OIDC data from the load balancer, validates it, and adds new headers as expected by Grafana.
    Some form of key caching may be useful and will be implemented later.
    """

    def __init__(self, aws_region: str, upstream: URL, ignore_auth: bool = False):
        """Creates a server for a given AWS region.
        """
        self._aws_region = aws_region
        self._ignore_auth = ignore_auth
        self._upstream = upstream
        self._key_url = URL(
            f"https://public-keys.auth.elb.{self._aws_region}.amazonaws.com/"
        )

    async def _setup_session(self, app):
        """Handle context sessions nicely.

        `See docs <https://docs.aiohttp.org/en/latest/client_advanced.html#persistent-session>`_"""
        self._key_session = ClientSession(raise_for_status=True)
        self._upstream_session = ClientSession(raise_for_status=True)
        yield
        await asyncio.gather(self._key_session.close(), self._upstream_session.close())

    def run_app(self):
        if self._ignore_auth:
            logger.warning("Authentication check disabled!")
        app = web.Application(middlewares=[self.auth_middleware])
        app.router.add_route("*", "/{tail:.*}", self.handle_request)
        app.cleanup_ctx.append(self._setup_session)
        web.run_app(app)

    async def _decode_data(self, oidc_data: str) -> Mapping[str, str]:
        """ Returns the payload of the OIDC data sent by the ALB

        :param oidc_data: OIDC data from alb
        :return: payload
        :raise: jwt.exceptions.ExpiredSignatureError: If the token is not longer valid
        """
        kid, alg = _kid_from_oidc_data(oidc_data)

        async with self._key_session.get(self._key_url.join(kid)) as response:
            pub_key = await response.text()

        payload = jwt.decode(oidc_data, pub_key, algorithms=[alg])
        return payload

    async def _auth_payload(self, request: web.Request) -> Optional[Mapping[str, str]]:
        """Returns the authentication payload, if any, as a dictionary.

        Catches exceptions from decoding the payload and converts them to HTTP exceptions to be propagated.
        If authentication is disabled via :attr:`~_ignore_auth` doesn't verify anything and returns `None`.

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
            return await self._decode_data(oidc_data)
        except ExpiredSignatureError:
            logger.warning("Got expired token. Dropping request.")
            raise HTTPUnauthorized()
        except DecodeError as e:
            logger.warning("Couldn't decode token. Dropping request.")
            logger.debug("Couldn't decode token: %s" % e)
            raise HTTPBadRequest()

    async def handle_request(self, request):
        upstream_url = self._upstream.join(request.url.relative())
        upstream_request = self._upstream_session.request(
            url=upstream_url,
            method=request.method,
            headers=clean_response_headers(request.headers),
            params=request.query,
            data=request.content,
            allow_redirects=False,
        )

        async with upstream_request as upstream_response:
            response = web.StreamResponse(
                status=upstream_response.status, headers=upstream_response.headers
            )

            await response.prepare(request)

            async for data, last in upstream_response.content.iter_chunks():
                await response.write(data)

            await response.write_eof()
            return response

    @web.middleware
    async def auth_middleware(self, request, handler):
        # payload = await self._auth_payload(request)
        resp = await handler(request)
        return resp
