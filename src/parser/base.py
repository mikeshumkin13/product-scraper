from abc import ABC, abstractmethod
from typing import List, Dict
from dataclasses import dataclass


class BaseParser(ABC):
    @abstractmethod
    def fetch_page(self, url: str) -> str:
        """Загружает HTML страницу"""
        pass

    @abstractmethod
    def parse(self, html: str) -> List[Dict]:
        """Парсит HTML и возвращает список товаров"""
        pass

    def run(self, url: str) -> List[Dict]:
        html = self.fetch_page(url)
        return self.parse(html)


@dataclass
class Product:
    """
    Класс продукта для унифицированного представления товара.
    """

    name: str
    url: str
    price: int | str  # int для чисел, str для форматированного вывода
