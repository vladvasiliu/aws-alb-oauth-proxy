import asyncio
import argparse
import logging
import sys
from concurrent.futures.process import ProcessPoolExecutor

from aiohttp import web

from helpers import _aws_region
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

logger = logging.getLogger("main")
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError("Invalid log level: %s" % loglevel)
logging.basicConfig(
    level=numeric_level, format="%(asctime)s %(processName)-22s %(levelname)-8s %(name)-15s %(message)s"
)


# Actual work

region = _aws_region()
if not region:
    logger.error("Could not detect AWS region. Are we running on AWS?")
    sys.exit(1)


def work():
    proxy = Proxy(aws_region=region, upstream=upstream, ignore_auth=ignore_auth)
    runner = proxy.runner()

    async def start():
        await runner.setup()
        site = web.TCPSite(runner, port=port, reuse_address=True, reuse_port=True)
        logger.debug("Started site...")
        await site.start()

    async def cleanup():
        await runner.cleanup()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    try:
        loop.run_until_complete(start())
        logger.debug("Looping forever...")
        loop.run_forever()
    except Exception as exc:
        logger.warning(f"Got exception: {exc}. Shutting down...")
        loop.run_until_complete(cleanup())
        loop.stop()


with ProcessPoolExecutor(max_workers=4) as executor:
    workers = {executor.submit(work) for _ in range(4)}
    for future in workers:
        try:
            future.result
        except Exception as exc:
            logger.warning(f"Worker {future} got an exception: {exc}")
        else:
            logger.info(f"Worker {future} is shut down.")
