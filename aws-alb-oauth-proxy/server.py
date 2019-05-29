import base64
import json
import logging
from typing import Mapping

from aiohttp import ClientSession, web
import jwt
from aiohttp.web_exceptions import (
    HTTPUnauthorized,
    HTTPProxyAuthenticationRequired,
    HTTPBadRequest,
)
from jwt import DecodeError, ExpiredSignatureError

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

    def __init__(self, aws_region: str):
        """Creates a server for a given AWS region.
        """
        self._aws_region = aws_region

    async def _setup_session(self, app):
        """Handle context sessions nicely.

        `See docs <https://docs.aiohttp.org/en/latest/client_advanced.html#persistent-session>`_"""
        self._key_session = ClientSession(raise_for_status=True)
        yield
        await self._key_session.close()

    def setup_app(self):
        app = web.Application(middlewares=[self.auth_middleware])
        app.router.add_route("*", "/", self.handle_request)
        app.cleanup_ctx.append(self._setup_session)
        web.run_app(app)

    # async def __aexit__(self, exc_type, exc_val, exc_tb):
    #     await self._key_session.close()
    #     await self._runner.cleanup()

    def _key_url(self, kid: str) -> str:
        return f"https://public-keys.auth.elb.{self._aws_region}.amazonaws.com/{kid}"

    async def decode_data(self, oidc_data: str) -> Mapping[str, str]:
        """ Returns the payload of the OIDC data sent by the ALB

        :param oidc_data: OIDC data from alb
        :return: payload
        :raise: jwt.exceptions.ExpiredSignatureError: If the token is not longer valid
        """
        kid, alg = _kid_from_oidc_data(oidc_data)

        async with self._key_session.get(self._key_url(kid)) as response:
            pub_key = await response.text()

        payload = jwt.decode(oidc_data, pub_key, algorithms=[alg])
        return payload

    async def handle_request(self, request):
        return web.Response(text="sup")

    @web.middleware
    async def auth_middleware(self, request, handler):
        headers = request.headers
        try:
            oidc_data = headers["X-Amzn-Oidc-Data"]
        except KeyError:
            logger.warning("No X-Amzn-Oidc-Data header present. Dropping request.")
            raise HTTPProxyAuthenticationRequired()
        try:
            payload = await self.decode_data(oidc_data)
        except ExpiredSignatureError:
            logger.warning("Got expired token. Dropping request.")
            raise HTTPUnauthorized()
        except DecodeError as e:
            logger.warning("Couldn't decode token. Dropping request.")
            logger.debug("Couldn't decode token: %s" % e)
            raise HTTPBadRequest()
        resp = await handler(request)
        resp.text += payload
        return resp


if __name__ == "__main__":
    Proxy("eu-west-3").setup_app()
