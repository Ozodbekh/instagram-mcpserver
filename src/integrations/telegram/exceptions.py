class TelegramError(Exception):
    pass


class TelegramNotConfigured(TelegramError):
    pass


class TelegramUnavailable(TelegramError):
    pass


class TelegramRefused(TelegramError):
    pass
