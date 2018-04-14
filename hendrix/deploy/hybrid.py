from .tls import HendrixDeployTLS
from .cache import HendrixDeployCache


class HendrixDeployHybrid(HendrixDeployTLS, HendrixDeployCache):
    pass
