from .ssl import HendrixDeploySSL
from .cache import HendrixDeployCache


class HendrixDeployHybrid(HendrixDeploySSL, HendrixDeployCache):
    pass
