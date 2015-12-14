from twisted.logger import Logger

logger = Logger()

logger.warn("hendrix.resources is being deprecated.  Please see hendrix.facilities.resources.")

from hendrix.facilities.resources import *