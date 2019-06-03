|Scrutinizer| |Style badge| |Docs badge| |License badge|


aws-alb-oauth-proxy
===================

This is a proxy that sits between an application that doesn't handle JWT and an authentication proxy.
It decodes the JWT and sends the relevant information as HTTP headers.

It can be seen as a translation layer between JWT and classic Auth Proxy.

Usage
-----

See `the docs <https://aws-alb-oauth-proxy.readthedocs.io/en/latest>`_ for details.

Docker
~~~~~~

`There's a build available on Docker Hub <https://hub.docker.com/r/vladvasiliu/aws-alb-oauth-proxy>`_.

.. code-block::

  $ docker run vladvasiliu/aws-alb-oauth-proxy:latest http://upstream.url

For a quick help:

.. code-block::

  $ docker run vladvasiliu/aws-alb-oauth-proxy:latest -h

From source
~~~~~~~~~~~

.. code-block::

  $ cd aws-alb-oauth-proxy/
  $ pip install -r requirements.txt
  $ python aws_alb_oauth_proxy http://upstream.url

For a quick help:

.. code-block::

  $ python aws_alb_oauth_proxy -h


Use case
--------
The use case is running Grafana behind an AWS Application Load Balancer with OpenID Connect authentication.

Grafana can do OIDC authentication itself, but cannot delegate it to a proxy nor handle JWT authentication.
Work is in progress to implement this (see `Grafana PR #15187 <https://github.com/grafana/grafana/pull/15187>`_)


Development
-----------

This is implemented in Python 3.7 using `asyncio <https://docs.python.org/3/library/asyncio.html>`_ and `aiohttp <https://aiohttp.readthedocs.io/en/stable/>`_.

This project use the `Black code style <https://black.readthedocs.io/en/stable/the_black_code_style.html>`_.

Issues and pull requests may be submitted through GitHub.


Useful documentation
--------------------
* `Grafana Auth Proxy Authentication <https://grafana.com/docs/auth/auth-proxy/>`_
* `Authenticate users using an application load balancer <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html#user-claims-encoding>`_

License
-------
This code is distributed under GPLv3. See `LICENSE <LICENSE>`_ for the full text.

.. |Scrutinizer| image:: https://scrutinizer-ci.com/g/vladvasiliu/aws-alb-oauth-proxy/badges/quality-score.png?b=master
   :target: https://scrutinizer-ci.com/g/vladvasiliu/aws-alb-oauth-proxy/
.. |Style badge| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/python/black
.. |License badge| image:: https://img.shields.io/github/license/vladvasiliu/aws-alb-oauth-proxy.svg
   :target: LICENSE
.. |Docs badge| image:: https://readthedocs.org/projects/aws-alb-oauth-proxy/badge/?version=latest
   :target: https://aws-alb-oauth-proxy.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

