class InstagramError(Exception):
    pass


class InstagramUnavailable(InstagramError):
    pass


class InstagramTokenInvalid(InstagramError):
    pass


class InstagramPermissionDenied(InstagramError):
    pass


class InstagramThrottled(InstagramError):
    pass


class InstagramRefused(InstagramError):
    pass
