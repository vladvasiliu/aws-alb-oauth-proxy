Introduction
============

What it is
----------

This is a reverse proxy meant to be run between an AWS Application load balancer with authentication and Grafana.
It reads the JWT sent by the ALB and translates it to an HTTP header understood by Grafana.

As of May 2019 there was no native support for this in Grafana, so I rolled my own.

A pull request is in progress to add this, follow it here: `PR 15187 <https://github.com/grafana/grafana/pull/15187>`_.


Motivation
----------

We use extensively Single Sign-On for most of our web applications. There are two limitations with Grafana:

#. Grafana supports OpenID Connect, but it's not unable to get additional information from a directory upon login,
   for e.g. to attribute rights according to group membership;
#. When using an ALB, it sets a JTW header which Grafana doesn't understand. The user has to login again.


Quick start
-----------

A Docker container is available `on Docker hub <https://cloud.docker.com/u/vladvasiliu/repository/docker/vladvasiliu/aws-alb-oauth-proxy/general>`_::

    $ docker run vladvasiliu/aws-alb-oauth-proxy:latest http://grafana.internal:3000

