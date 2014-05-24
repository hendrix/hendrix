from twisted.internet import ssl
from twisted.application import internet


# for testing purposes create a private key and a self signed certificate
# http://blog.vrplumber.com/b/2004/09/26/howto-create-an-ssl/
#     First, we generate a private key file:
#         openssl genrsa > key.pem
#     Then we generate a self-signed SSL certificate:
#         openssl req -new -x509 -key key.pem -out cacert.pem -days 1000


class SSLServer(internet.SSLServer):

    def __init__(self, port, site, key, cacert):
        sslContext = ssl.DefaultOpenSSLContextFactory(
            key,  # '/path/to/key.pem',
            cacert,  # '/path/to/cacert.pem',
        )
        internet.SSLServer.__init__(
            self,
            port,  # integer port
            site,  # our site object, see the web howto
            contextFactory=sslContext,
        )

        self.factory = site
