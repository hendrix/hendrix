class ThreadHasNoResponse(RuntimeError):
    pass


class RedisException(AttributeError):
    """
    Raised if a user tries to use redis-only features without redis available.
    """
