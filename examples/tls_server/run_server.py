# A sample server using TLS with either RSA or EC.
# To use this, first run either gen-ec.py or gen-rsa.py (or both).

from hendrix.deploy.ssl import HendrixDeployTLS
from hendrix.facilities.services import SpecifiedCurveContextFactory


# Taken directly from PEP333, except response string is changed (and is bytes instead of str).
def simple_app(environ, start_response):
    """Simplest possible application object"""
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b'Bambino!\n']

ec_deployer = HendrixDeployTLS("start",
                               {"wsgi": simple_app, "https_port": 8443},
                               key="ec-key.pem",
                               cert="ec-certificate.pem",
                               context_factory=SpecifiedCurveContextFactory,
                               context_factory_kwargs={"curve_name": "secp256k1"}
                               )

rsa_deployer = HendrixDeployTLS("start",
                                {"wsgi": simple_app, "https_port": 8443},
                                key="rsa-key.pem",
                                cert="rsa-certificate.pem",
                                )

# Uncomment this to use the elliptic curve variant.
# ec_deployer.run()
rsa_deployer.run()
