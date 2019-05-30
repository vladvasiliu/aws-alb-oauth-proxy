import base64
import json

from multidict import CIMultiDictProxy, CIMultiDict


DEFAULT_REMOVED_RESPONSE_HEADERS = {
    "Content-Length",
    "Content-Encoding",
    "Transfer-Encoding",
}


def clean_response_headers(headers: CIMultiDict) -> CIMultiDictProxy:
    """Removes HTTP headers from an upstream response.

    :param headers: A CIMultiDict containing the response headers to be cleaned.
    :return: A CIMultiDictProxy containing the clean headers.
    """
    clean_headers = headers.copy()
    for header in DEFAULT_REMOVED_RESPONSE_HEADERS:
        clean_headers.popall(header, None)
    return CIMultiDictProxy(clean_headers)


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
