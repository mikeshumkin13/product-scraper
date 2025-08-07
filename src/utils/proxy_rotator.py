import json
import os
import random


def get_random_proxy() -> dict:
    """
    Возвращает словарь прокси с авторизацией.
    :return: {'http': ..., 'https': ...}
    """
    path = os.path.join(os.path.dirname(__file__), "proxies.json")
    with open(path, "r", encoding="utf-8") as f:
        proxies = json.load(f)

    proxy = random.choice(proxies)
    auth = f"{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    return {"http": f"http://{auth}", "https": f"http://{auth}"}
