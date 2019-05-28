from aiohttp import ClientSession
import base64
import json
import jwt
import logging
from typing import Mapping


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


class Server:
    """This is basically a reverse proxy that translates some headers. We don't care about cookies or sessions.

    This takes the OIDC data from the load balancer, validates it, and adds new headers as expected by Grafana.
    Some form of key caching may be useful and will be implemented later.
    """

    def __init__(self, aws_region: str):
        """Creates a server for a given AWS region.
        """
        self._aws_region = aws_region

    async def __aenter__(self):
        self._key_session = ClientSession(raise_for_status=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._key_session.close()

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
