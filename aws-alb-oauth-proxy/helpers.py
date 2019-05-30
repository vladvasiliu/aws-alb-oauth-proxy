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
