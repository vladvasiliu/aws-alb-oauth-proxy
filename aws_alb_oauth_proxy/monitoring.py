from prometheus_client import Counter, Histogram

REQUEST_HISTOGRAM = Histogram("request_latency_seconds", "Latency of request handling")
UPSTREAM_STATUS_COUNTER = Counter(
    "upstream_response_status", "Count of upstream responses by method and status returned", ["method", "status"]
)
