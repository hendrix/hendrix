class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'


    @classmethod
    def end(cls, color, message):
        print '%(color)s%(message)s\033[0m' % {'color': color, 'message': message}

    @classmethod
    def red(cls, message):
        cls.end(cls.FAIL, message)

    @classmethod
    def blue(cls, message):
        cls.end(cls.OKBLUE, message)

    @classmethod
    def green(cls, message):
        cls.end(cls.OKGREEN, message)

    @classmethod
    def warning(cls, message):
        cls.end(cls.WARNING, message)
