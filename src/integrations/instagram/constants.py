API_BASE_URL = 'https://graph.instagram.com'

EXCHANGE_PATH = '/access_token'
REFRESH_PATH = '/refresh_access_token'

EXCHANGE_GRANT_TYPE = 'ig_exchange_token'
REFRESH_GRANT_TYPE = 'ig_refresh_token'

CONNECT_TIMEOUT_SECONDS = 3.05
READ_TIMEOUT_SECONDS = 15.0

INVALID_TOKEN_CODES = (190,)
PERMISSION_CODES = (10, 200)
RATE_LIMIT_CODES = (4, 17, 32, 613)
