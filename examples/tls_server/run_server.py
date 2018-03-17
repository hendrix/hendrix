# A sample server using TLS with either RSA or EC.
# To use this, first run either gen-ec.py or gen-rsa.py (or both).

from hendrix.deploy.ssl import HendrixDeployTLS
from hendrix.experience import hey_joe
from hendrix.facilities.services import SpecifiedCurveContextFactory
import sys
sys.path.append("../django_nyc_demo")
from hendrix_demo.wsgi import application as hendrix_demo_app

PORT = 8443

# EC variant
# deployer = HendrixDeployTLS("start",
#                                {"wsgi": hendrix_demo_app, "https_port": PORT},
#                                key="ec-key.pem",
#                                cert="ec-certificate.pem",
#                                context_factory=SpecifiedCurveContextFactory,
#                                context_factory_kwargs={"curve_name": "secp256k1"}
#                                )

# RSA variant
deployer = HendrixDeployTLS("start",
                                {"wsgi": hendrix_demo_app, "https_port": PORT},
                                key="rsa-privkey.pem",
                                cert="rsa-certificate.pem",
                                )


wss_service = hey_joe.WSSWebSocketService("127.0.0.1", 9443,
                                          allowedOrigins=["https://localhost:{}".format(PORT)])
deployer.add_tls_websocket_service(wss_service)
deployer.run()
