Interaction with Grafana
========================

The main sources of documentation are:

#. `Authenticate Users Using an Application Load Balancer - User Claims Encoding and Signature Verification <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html#user-claims-encoding>`_
#. `Grafana Auth Proxy Authentication <https://grafana.com/docs/auth/auth-proxy/>`_

Configuring the AWS Load balancer to authenticate with your identity provider is outside the scope of this document,
but you can learn about it by following the first link above.

Once you have the ALB authentication running, you have to configure Grafana to accept the header sent by the proxy.

The default is to use the user's email and send it in the ``X-WEBAUTH-USER`` flag, which is the one in the Grafana docs.

.. note::

    It will be possible to choose which field of the ``oidc-data`` payload to send and how to name the HTTP header sent
    upstream. *This is not yet implemented.*

    This is the field referenced in the :ref:`note below <search_filter>`.


* If you don't have LDAP setup, user configuration stops here and you'll have to assign the rights manually to each user.
* If you have LDAP setup, this is the field that will be used in the directory search to retrieve the user's other
  attributes, such as actual username as rights.

.. attention::

   If you don't have LDAP setup, you may want to create an admin user before activating proxy authentication, as this
   will be the only way to login and any new user will only have *Viewer* rights.

Example Grafana configuration
-----------------------------

Below is a config excerpt from the Grafana server I run, configured to query ActiveDirectory to give users access rights
according to their group membership:

.. code-block:: ini
    :caption: grafana.ini

    [auth.proxy]
    enabled = true
    header_name = X-WEBAUTH-USER
    header_property = email
    auto_sign_up = true
    ldap_sync_ttl = 60
    whitelist = 127.0.0.1           # Proxy is running on the same host

    ...

    [auth.ldap]
    enabled = true
    config_file = /etc/grafana/ldap.toml
    allow_sign_up = true


.. attention::
   :name: search_filter

    The ``search_filter`` below must match the field extracted from the JWT sent by the load balancer --- by default the
    email.

.. code-block:: ini
    :caption: ldap.toml

    [[servers]]
    host = "ad.example.com"
    port = 3269
    use_ssl = true
    start_tls = false
    ssl_skip_verify = false
    root_ca_cert = "/path/to/certificate.crt"

    # Search user bind dn
    bind_dn = "grafana@example.com"
    bind_password = """70p53cr37"""

    # User search filter, for example "(cn=%s)" or "(sAMAccountName=%s)" or "(uid=%s)"
    search_filter = "(mail=%s)"

    # An array of base dns to search through
    search_base_dns = ["ou=users,dc=example,dc=com"]

    [servers.attributes]
    name = "givenName"
    surname = "sn"
    username = "sAMAccountName"
    member_of = "memberOf"
    email =  "mail"

    # Map ldap groups to grafana org roles
    [[servers.group_mappings]]
    group_dn = "CN=Grafana-Admin,OU=Groups,DC=example,DC=com"
    org_role = "Admin"
    # The Grafana organization database id, optional, if left out the default org (id 1) will be used
    # org_id = 1

    #[[servers.group_mappings]]
    #group_dn = "cn=users,dc=grafana,dc=org"
    #org_role = "Editor"

    [[servers.group_mappings]]
    # If you want to match all (or no ldap groups) then you can use wildcard
    group_dn = "CN=Grafana-Viewers,OU=Groups,DC=example,DC=com"
    #group_dn = "*"
    org_role = "Viewer"
