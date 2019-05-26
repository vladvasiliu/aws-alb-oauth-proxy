from aiohttp import ClientSession
import base64
import json
import jwt
import logging


logger = logging.getLogger(__name__)


class Server:
    def __init__(self, aws_region: str):
        """Creates a server for a given AWS region.
        """
        self._aws_region = aws_region

    async def __aenter__(self):
        self._key_session = ClientSession(raise_for_status=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._key_session.close()

    async def decode_data(self, oidc_data: str):
        """Decodes the JWT tokens in the x-amzn-oidc-data header sent by AWS ELB

        `AWS Documentation
        <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html#user-claims-encoding>`_
        """
        headers = oidc_data.split(".")[0]

        # Get Key ID
        decoded_headers = base64.b64decode(headers).decode("utf-8")
        json_headers = json.loads(decoded_headers)
        kid = json_headers["kid"]

        # Get public key
        url = (
            "https://public-keys.auth.elb." + self._aws_region + ".amazonaws.com/" + kid
        )
        async with self._key_session.get(url) as response:
            pub_key = await response.text()
        payload = jwt.decode(oidc_data, pub_key, algorithms=["ES256"])
        return payload
