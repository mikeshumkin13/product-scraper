import requests
from typing import List, Dict
import urllib.parse


def search_wildberries(query: str) -> List[Dict]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }

    encoded_query = urllib.parse.quote(query)
    url = f"https://search.wb.ru/exactmatch/ru/common/v5/search?query={encoded_query}&resultset=catalog&sort=popular&page=1&limit=20"

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise Exception(f"🌐 Ошибка запроса к Wildberries API: {e}")
    except ValueError:
        raise Exception("⚠️ Не удалось разобрать JSON-ответ от Wildberries")

    if "data" not in data or "products" not in data["data"]:
        return []

    products = []
    for item in data["data"]["products"]:
        name = item.get("name", "Без названия")
        price = item.get("priceU", 0) / 100
        id = item.get("id")
        url = f"https://www.wildberries.ru/catalog/{id}/detail.aspx"

        products.append({
            "name": name,
            "price": f"{price:.2f} ₽",
            "url": url
        })

    return products


