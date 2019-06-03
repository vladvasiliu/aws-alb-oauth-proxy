Installation
============

There are two ways of running the proxy:

#. Docker, which is the recommended way
#. Run the python code directly

In both cases it expects some parameters. The up to date parameter list as well as their defaults can be found with the
``-h`` flag.


Docker
------

A docker container is available on Docker Hub. There are two tags:

``latest``
  This tag follows the GitHub ``master`` branch. This is not guaranteed to be stable, although it should at least start.
``vX.Y``
  This is the *release* tag and supposed to be stable.

.. code-block:: sh

    $ docker run vladvasiliu/aws-alb-oauth-proxy:latest http://grafana.internal:3000


Source
------

.. note::

   This code requires Python 3.7.

You can `get the code from GitHub <https://github.com/vladvasiliu/aws-alb-oauth-proxy>`_ and run it as is.




``aws_alb_oauth_proxy`` is a Python module and can be run directly::

    $ git clone git@github.com:vladvasiliu/aws-alb-oauth-proxy.git
    $ cd aws-alb-oauth-proxy
    $ pip install -r requirements.txt
    $ python aws_alb_oauth_proxy http://grafana.url:3000

You may however want to use this inside a virtual environment. If you're unfamiliar with ``virtualenv``, `see the docs
<https://virtualenv.pypa.io/en/stable/>`_.
