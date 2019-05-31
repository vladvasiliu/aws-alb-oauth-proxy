import argparse
import logging

from server import Proxy

# Command line arguments

parser = argparse.ArgumentParser(
    description="Decode AWS ALB OIDC JWT to Proxy Auth for Grafana",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("upstream", help="Upstream server URL: scheme://host:port")
parser.add_argument("-p", "--port", type=int, default=8080, help="Port to listen on.")
parser.add_argument("--ignore-auth", action="store_true", help="Whether to ignore the JWT token")
parser.add_argument(
    "--loglevel", default="info", choices=["debug", "info", "warning", "error", "critical"], help="Logging verbosity"
)
parser.add_argument("--logtz", default="local", choices=["utc", "local"], help="Time zone to use for logging")

args = parser.parse_args()

upstream = args.upstream
port = args.port
ignore_auth = args.ignore_auth

loglevel = args.loglevel


# Logging

logger = logging.getLogger(__name__)
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError("Invalid log level: %s" % loglevel)
logging.basicConfig(level=numeric_level)


# Actual work

proxy = Proxy("eu-west-3", upstream=upstream, ignore_auth=ignore_auth)
proxy.run_app()
