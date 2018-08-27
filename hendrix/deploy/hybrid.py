from .cache import HendrixDeployCache
from .tls import HendrixDeployTLS


class HendrixDeployHybrid(HendrixDeployTLS, HendrixDeployCache):
    pass
