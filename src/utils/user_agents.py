import random

# Подборка реальных User-Agent заголовков с разных устройств и браузеров
USER_AGENTS = [
    # Chrome на Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    # Firefox на Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:102.0) "
    "Gecko/20100101 Firefox/102.0",
    # Safari на Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    # Chrome на Android
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
    # Edge на Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.50",
]


def get_random_user_agent() -> str:
    """
    Возвращает случайный User-Agent из набора.

    :return: строка User-Agent
    """
    return random.choice(USER_AGENTS)
